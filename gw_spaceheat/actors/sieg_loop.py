import time
from typing import List
import asyncio
import uuid
from enum import auto
from data_classes.house_0_names import H0CN
from gwproto.message import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.named_types import FsmFullReport, SingleReading, AnalogDispatch
from result import Ok, Result
from gw.enums import GwStrEnum
from transitions import Machine
from actors.scada_actor import ScadaActor
from actors.scada_interface import ScadaInterface
from enums import LogLevel
from named_types import Glitch, SingleMachineState

from transitions import Machine
class SiegState(GwStrEnum):
    KeepingMore = auto()
    KeepingLess = auto()
    SteadyBlend = auto()
    FullySend = auto()
    FullyKeep = auto() 

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "valve.state"
class SiegEvent(GwStrEnum):
    StartKeepingMore = auto()
    StartKeepingLess = auto()
    StopKeepingMore = auto()
    StopKeepingLess = auto()
    ResetToFullySend = auto()
    ResetToFullyKeep = auto()

class SiegLoop(ScadaActor):
    """
    ```
              ├── HpLoopOnOff relay
              └── HpLoopKeepSend relay
    ```
    """
    FULL_RANGE_S = 70
    RESET_S = 10

    def __init__(self, name: str, services: ScadaInterface):
        super().__init__(name, services)
        self.percent_keep: int = 100
        self.resetting = False
        self.state: SiegState = SiegState.FullyKeep
        self._movement_task = None # Track the current movement task
        self.move_start_s: float = 0
        self.latest_move_duration_s: float = 0
        # Define transitions with callback
        self.transitions = [
            {"trigger": "StartKeepingMore", "source": "FullySend", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StartKeepingMore", "source": "SteadyBlend", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StartKeepingMore", "source": "KeepingLess", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StartKeepingMore", "source": "KeepingMore", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StopKeepingMore", "source": "KeepingMore", "dest": "SteadyBlend", "before": "before_keeping_steady"},
            {"trigger": "StartKeepingLess", "source": "FullyKeep", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StartKeepingLess", "source": "SteadyBlend", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StartKeepingLess", "source": "KeepingMore", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StartKeepingLess", "source": "KeepingLess", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StopKeepingLess", "source": "KeepingLess", "dest": "SteadyBlend", "before": "before_keeping_steady"},
            {"trigger": "ResetToFullySend", "source": "KeepingLess", "dest": "FullySend", "before": "before_keeping_steady"},
            {"trigger": "ResetToFullyKeep", "source": "KeepingMore", "dest": "FullyKeep", "before": "before_keeping_steady"},
        ]
        self.machine = Machine(
            model=self,
            states=SiegState.values(),
            transitions=self.transitions,
            initial=SiegState.FullyKeep,
            send_event=True, # Enable event passing to callbacks
        )

    def start(self) -> None:
        """ Move to full send"""
        # Generate a new task ID for this movement
        new_task_id = str(uuid.uuid4())[-4:]
        self._current_task_id = new_task_id
        target_percent = 0
        self.log(f"Task {new_task_id}: target {target_percent}")
        self._current_task_id = new_task_id
        self._movement_task = asyncio.create_task(
            self._move_to_target_percent_keep(target_percent, new_task_id)
        )  

    def stop(self) -> None:
        """ Required method, used for stopping tasks. Noop"""
        ...

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...
    ##############################################
    # State machine mechanics
    ##############################################

    # Transition callback methods
    def before_keeping_more(self, event):
        self.change_to_hp_keep_more()
        self.sieg_valve_active()
        self.move_start_s = time.time()

    def before_keeping_less(self, event):
        self.change_to_hp_keep_less()
        self.sieg_valve_active()
        self.move_start_s = time.time()

    def before_keeping_steady(self, event):
        # Logic for steady blend state (including FullySend and FullyKeep)
        self.sieg_valve_dormant()
        self.latest_move_duration_s = time.time() - self.move_start_s

    def trigger_event(self, event: SiegEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state

        if self.resetting:
            raise Exception("Do not interrupt resetting to fully send or fully keep!")

        # Trigger the state machine transition
        self.trigger(event)

        self.log(f"{event}: {orig_state} -> {self.state}")

        self._send_to(
            self.primary_scada,
            SingleMachineState(
                MachineHandle=self.node.handle,
                StateEnum=SiegState.enum_name(),
                State=self.state,
                UnixMs=now_ms,
                Cause=event
            )
        )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        from_node = self.layout.node(message.Header.Src, None)
        if from_node is None:
            return Ok(False)
        payload = message.Payload
        match payload:
            case AnalogDispatch():
                try:
                    asyncio.create_task(self.process_analog_dispatch(from_node, payload), name="analog_dispatch")
                except Exception as e:
                    self.log(f"Trouble with process_analog_dispatch: {e}")
            case FsmFullReport():
                ... # got report back from relays
            case _: 
                self.log(f"{self.name} received unexpected message: {message.Header}"
            )
        return Ok(True)

    async def process_analog_dispatch(self, from_node: ShNode, payload: AnalogDispatch) -> None:    
        if from_node != self.boss:
            self.log(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
            return

        if self.boss.handle != payload.FromHandle:
            self.log(f"boss's handle {self.boss.handle} does not match payload FromHandle {payload.FromHandle}")
            return

        target_percent = payload.Value
        self.log(f"Received command to set valve to {target_percent}% keep")

        # Generate a new task ID for this movement
        new_task_id = str(uuid.uuid4())[-4:]
        self._current_task_id = new_task_id
        
        # Cancel any existing movement task
        if hasattr(self, '_movement_task') and self._movement_task and not self._movement_task.done():
            self.log(f"Cancelling previous movement from {self.percent_keep}% to new target {target_percent}%")
            self._movement_task.cancel()
            
            # Wait for the task to actually complete
            try:
                # Use a timeout to avoid waiting forever if something goes wrong
                await asyncio.wait_for(self._movement_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                self.log("Cancelled previous task")
            
            # Ensure proper state cleanup regardless of how the task ended
            if self.state == SiegState.KeepingMore:
                self.trigger_event(SiegEvent.StopKeepingMore)
                self.log(f"Triggered StopKeepingMore after cancellation")
            elif self.state == SiegState.KeepingLess:
                self.trigger_event(SiegEvent.StopKeepingLess)
                self.log(f"Triggered StopKeepingLess after cancellation")

        # Create a new task for the movement
        self._movement_task = asyncio.create_task(
            self._move_to_target_percent_keep(target_percent, new_task_id)
        )  

    async def _move_to_target_percent_keep(self, target_percent: int, task_id: str) -> None:
        """Move the valve to the target percent keep value."""
        if self.percent_keep == target_percent:
            self.log(f"Already at target {target_percent}%")
            return
            
        # Determine direction
        moving_to_more_keep = self.percent_keep < target_percent
    
        # Wait a moment to ensure the state machine has settled
        await asyncio.sleep(0.2)
        
        # Set the appropriate state
        try:
            if moving_to_more_keep:
                self.log(f"Starting movement to MORE keep ({self.percent_keep}% -> {target_percent}%)")
                self.trigger_event(SiegEvent.StartKeepingMore)
                # Now process the movement in a loop
                while self.percent_keep < target_percent:
                    # Check if this task has been superseded
                    if task_id != self._current_task_id:
                        self.log(f"Task {task_id} has been superseded, stopping")
                        break
                        
                    await self._keep_one_percent_more(task_id)
                    # Allow for cancellation to be processed
                    await asyncio.sleep(0)
            else:
                self.log(f"Starting movement to LESS keep ({self.percent_keep}% -> {target_percent}%)")
                self.trigger_event(SiegEvent.StartKeepingLess)
                
                # Now process the movement in a loop
                while self.percent_keep > target_percent:
                    # Check if this task has been superseded
                    if task_id != self._current_task_id:
                        self.log(f"Task {task_id} has been superseded, stopping")
                        break
                        
                    await self._keep_one_percent_less(task_id)
                    # Allow for cancellation to be processed
                    await asyncio.sleep(0)

            # Complete the movement only if we're still the current task
            if task_id == self._current_task_id:
                if moving_to_more_keep and self.state == SiegState.KeepingMore:
                    self.trigger_event(SiegEvent.StopKeepingMore)
                elif not moving_to_more_keep and self.state == SiegState.KeepingLess:
                    self.trigger_event(SiegEvent.StopKeepingLess)
                    
                self.log(f"Movement completed: {self.percent_keep}% keep")

        except asyncio.CancelledError:
            self.log(f"Movement cancelled at {self.percent_keep}%")
            # Let the cancellation propagate to the caller
            raise
        
        except Exception as e:
            self.log(f"Error during movement: {e}")
            # Make sure to clean up state
            if self.state == SiegState.KeepingMore:
                self.trigger_event(SiegEvent.StopKeepingMore)
            elif self.state == SiegState.KeepingLess:
                self.trigger_event(SiegEvent.StopKeepingLess)

    async def _keep_one_percent_less(self, task_id: str) -> None:
        # Check if we're still the current task
        if task_id != self._current_task_id:
            return
        if self.state != SiegState.KeepingLess:
            raise Exception(f"Only call _keep_one_percent_less in state KeepingLess, not {self.state}")
        sleep_s = self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)

        # Check again if we're still the current task after sleeping
        if task_id != self._current_task_id:
            return
        
        self.percent_keep = orig_keep - 1
        self.log(f"{self.percent_keep}% keep")
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=H0CN.hp_keep,
                Value=self.percent_keep,
                ScadaReadTimeUnixMs=int(time.time() *1000)
            )
        )

    async def _keep_one_percent_more(self, task_id: str) -> None:
        # Check if we're still the current task
        if task_id != self._current_task_id:
            return
        if self.state != SiegState.KeepingMore:
            raise Exception(f"Only call _keep_one_percent_more in state KeepingMore, not {self.state}")
        sleep_s = self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)

        # Check again if we're still the current task after sleeping
        if task_id != self._current_task_id:
            return
        
        self.percent_keep = orig_keep + 1
        self.log(f"{self.percent_keep}% keep")
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=H0CN.hp_keep,
                Value=self.percent_keep,
                ScadaReadTimeUnixMs=int(time.time() *1000)
            )
        )

    def keep_harder(self) -> None:
        if self.state != SiegState.FullyKeep:
            self.log("Use when in FullyKeep")
            return
        self.change_to_hp_keep_more()
        self.sieg_valve_active()
        self._send_to(
                self.primary_scada,
                Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Info,
                    Summary="keep 1 second more",
                    Details=f"from fully keep w percent_keep {self.percent_keep}%, keep 1 second more"
                )
            )
        self.log(f"keeping for 1 second more")
        time.sleep(1)
        self.sieg_valve_dormant()

    def send_harder(self) -> None:
        if self.state != SiegState.FullySend:
            self.log("Use when in FullySend")
            return
        self.change_to_hp_keep_less()
        self.sieg_valve_active()
        self.log(f"sending for 1 second more")
        self._send_to(
                self.primary_scada,
                Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Info,
                    Summary="send 1 second more",
                    Details=f"from fully send w percent_keep {self.percent_keep}%, send 1 second more"
                )
            )
        time.sleep(1)
        self.sieg_valve_dormant()

