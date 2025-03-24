import time
from typing import List
import asyncio
from enum import auto
from data_classes.house_0_names import H0CN, H0N
from gwproto.message import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.named_types import FsmFullReport, SingleReading, AnalogDispatch
from gwproto.enums import ChangeRelayState
from result import Ok, Result
from gw.enums import GwStrEnum
from transitions import Machine
from actors.scada_actor import ScadaActor
from actors.scada_interface import ScadaInterface
from enums import LogLevel
from named_types import FsmEvent, Glitch, SingleMachineState

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

        # Define transitions with callback
        self.transitions = [
            {"trigger": "StartKeepingMore", "source": "FullySend", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StartKeepingMore", "source": "SteadyBlend", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StartKeepingMore", "source": "KeepingLess", "dest": "KeepingMore", "before": "before_keeping_more"},
            {"trigger": "StopKeepingMore", "source": "KeepingMore", "dest": "SteadyBlend", "before": "before_keeping_steady"},
            {"trigger": "StartKeepingLess", "source": "FullyKeep", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StartKeepingLess", "source": "SteadyBlend", "dest": "KeepingLess", "before": "before_keeping_less"},
            {"trigger": "StartKeepingLess", "source": "KeepingMore", "dest": "KeepingLess", "before": "before_keeping_less"},
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
        """ Required method, used for starting long-lived tasks. Noop."""
        asyncio.create_task(self._reset_to_fully_send())

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
        
    def before_keeping_less(self, event):
        self.change_to_hp_keep_less()
        self.sieg_valve_active()
        
    def before_keeping_steady(self, event):
        # Logic for steady blend state (including FullySend and FullyKeep)
        self.sieg_valve_dormant()
        
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
            case _: 
                self.log(f"{self.name} received unexpected message: {message.Header}"
            )
        return Ok(True)
    
    async def process_analog_dispatch(self, from_node: ShNode, payload: AnalogDispatch) -> None:    
        if from_node != self.boss:
            #raise Exception(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
            self.log(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
        if self.boss.handle != payload.FromHandle:
            self.log(f"boss's handle {self.boss.handle} does not match payload FromHandle {payload.FromHandle}")
        # don't interrupt a reset 
        orig_percent_keep = self.percent_keep
        orig_state = self.state
        if self.resetting:
            if orig_state == SiegState.KeepingMore:
                wait_s = 6 + self.FULL_RANGE_S * (100 -orig_percent_keep) / 100
                self.log(f"Waiting {wait_s} while resetting to full keep") 
            else:
                wait_s = 6 + self.FULL_RANGE_S * orig_percent_keep / 100
                self.log(f"Waiting {wait_s} while resetting to full send") 
            # wait for the resetting to finish
            await asyncio.sleep(wait_s)
        if self.resetting:
            self._send_to(
                self.primary_scada,
                Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Info,
                    Summary=f"SiegLoop ignored AnalogDispatch to set HpKeep to {payload.Value} because it was resetting",
                    Details=f"Slept for {wait_s} seconds from {orig_percent_keep} % and state {orig_state}. Was still resetting!"
                )
            )
            self.log(f"SiegLoop ignored AnalogDispatch to set HpKeep to {payload.Value} because it was resetting")
            return
        # OK! now we can follow the directions
        if payload.Value == 100:
            await self._reset_to_fully_keep()
        elif payload.Value == 0:
            await self._reset_to_fully_send()
        elif self.percent_keep > payload.Value:
            if self.state != SiegState.KeepingLess:
                self.trigger_event(SiegEvent.StartKeepingLess)
            while self.percent_keep > payload.Value:
                await self._keep_one_percent_less()
            self.trigger_event(SiegEvent.StopKeepingLess)
        else:
            if self.state != SiegState.KeepingMore:
                self.trigger_event(SiegEvent.StartKeepingMore)
            while self.percent_keep < payload.Value:
                await self._keep_one_percent_more()
            self.trigger_event(SiegEvent.StopKeepingMore)

    async def _reset_to_fully_send(self) -> None:
        self.log(f"Resetting to full send from {self.percent_keep}")
        if self.state == SiegState.FullySend:
            self.log("Already in FullySend")
            return
        if self.state != SiegState.KeepingLess:
            self.trigger_event(SiegEvent.StartKeepingLess)
        # Now we are in KeepingLess
        self.resetting = True
        while self.percent_keep > 0:
            await self._keep_one_percent_less()

        # Wait a little longer to make sure
        await asyncio.sleep(self.RESET_S)

        # rest of the code is supposed to respect resetting
        if self.state != SiegState.KeepingLess:
            raise Exception(f"resetting {self.resetting} and state {self.state}; expecting KeepingLess")
        self.resetting = False
        self.trigger_event(SiegEvent.ResetToFullySend)

    async def _reset_to_fully_keep(self) -> None:
        self.log(f"Resetting to full keep from {self.percent_keep}")
        if self.state == SiegState.FullyKeep:
            self.log("Already in FullyKeep")
            return
        if self.state != SiegState.KeepingMore:
            self.trigger_event(SiegEvent.StartKeepingMore)
        # Now we are in KeepingMore
        self.resetting = True
        while self.percent_keep < 100:
            await self._keep_one_percent_more()

        # Wait a little longer to make sure
        await asyncio.sleep(self.RESET_S)

        # rest of the code is supposed to respect resetting
        if self.state != SiegState.KeepingMore:
            raise Exception(f"resetting {self.resetting} and state {self.state}; expecting KeepingMore")
        self.resetting = False
        self.trigger_event(SiegEvent.ResetToFullyKeep)

    async def _keep_one_percent_less(self) -> None:
        if self.state != SiegState.KeepingLess:
            raise Exception(f"Only call _keep_one_percent_less in state KeepingLess, not {self.state}")
        sleep_s = self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)
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

    async def _keep_one_percent_more(self) -> None:
        if self.state != SiegState.KeepingMore:
            raise Exception(f"Only call _keep_one_percent_more in state KeepingMore, not {self.state}")
        sleep_s = self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)
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