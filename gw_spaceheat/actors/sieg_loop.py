import time
from datetime import datetime
from typing import List, Literal, Optional, Sequence
import asyncio
import uuid
from enum import auto
from data_classes.house_0_names import H0CN
from gwproactor import MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto.message import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.named_types import FsmFullReport, SingleReading, AnalogDispatch
from result import Ok, Result
from gw.enums import GwStrEnum
from transitions import Machine
from actors.hp_boss import SiegLoopReady, HpBossState
from actors.scada_actor import ScadaActor
from actors.scada_interface import ScadaInterface
from enums import LogLevel
from named_types import (ActuatorsReady, Glitch, ResetHpKeepValue, SetLwtControlParams,
    SetTargetLwt, SingleMachineState,  SiegLoopEndpointValveAdjustment)

from transitions import Machine
class SiegValveState(GwStrEnum):
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
        return "sieg.valve.state"
    
class ValveEvent(GwStrEnum):
    StartKeepingMore = auto()
    StartKeepingLess = auto()
    StopKeepingMore = auto()
    StopKeepingLess = auto()
    ResetToFullySend = auto()
    ResetToFullyKeep = auto()

class SiegControlState(GwStrEnum):
    Initializing = auto() # Scada just started up
    Dormant = auto()  # Heat pump off
    MovingToKeep = auto()  # Moving to t2 position 
    MovingToFullSend = auto() # 
    Hover = auto()  # Waiting at t2 position
    Active = auto()  # Normal proportional control

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "sieg.control.state"

class ControlEvent(GwStrEnum):
    InitializationComplete = auto()
    HpTurnsOff = auto()
    HpPreparing = auto()
    ReachT2 = auto()
    ReachFullSend = auto()
    NeedLessKeep = auto()
    Blind = auto()


class SiegLoop(ScadaActor):
    """
    ```
              ├── HpLoopOnOff relay
              └── HpLoopKeepSend relay
    ```
    SiegLoop: Heat Pump Leaving Water Temperature Control System

    This class manages a Siegenthaler loop valve which controls the mixing ratio between:
    1. Water recirculating directly back to the heat pump (keep path)
    2. Water flowing to the heating distribution system (send path)

    Control Problem:
    ---------------
    The primary objective is to maintain a target leaving water temperature (LWT) from the heat 
    pump while optimizing overall system efficiency. The challenge involves:

    1. Physical Characteristics:
    - Recirculation loop (~7 feet of 1" pipe) with ~4 second travel time
    - Temperature sensors with ~5 second response time
    - Valve movement takes ~70 seconds for full 0-100% travel

    2. System Dynamics:
    - At 100% keep: All water recirculates back to heat pump, increasing LWT
    - At 0% keep: All water sent to distribution; LWT set by HP lift
    - System has inherent thermal lag and momentum

    Control Algorithm:
    ----------------
    The system implements a modified proportional control with anticipatory elements:

    1. Basic Proportional Control:
    - Adjusts valve position proportionally to difference between target and actual LWT
    - Positive difference (target > actual): Increase recirculation (more keep)
    - Negative difference (target < actual): Decrease recirculation (more send)

    2. Anticipatory Component:
    - Activates when approaching target (within AnticipatoryThresholdF)
    - Uses Lift (LWT-EWT) as an indicator of thermal momentum
    - Applies additional correction based on current heat transfer rate
    - Acts as a "look-ahead" to prevent overshooting the target

    3. Movement Constraints:
    - Limits movement to physically possible rates (valve travel speed)
    - Prevents hunting by ignoring small temperature fluctuations
    - Handles transitions when heat pump turns on/off

    4. Operational States:
    - Heat pump OFF: Default to 0% keep (all water to distribution)
    - Heat pump starting: 100% keep to establish stable operation
    - Normal operation: Continuous adjustment to maintain target LWT

    Control Parameters:
    -----------------
    - ProportionalGain: Main response factor to temperature differences
    - AnticipatoryGain: How strongly to factor in thermal momentum
    - AnticipatoryThresholdF: When to begin anticipatory corrections
    - MinLiftForAnticipation: Minimum heat transfer rate to consider

    The algorithm is designed to provide smooth, stable temperature control while 
    adapting to both rapid and gradual changes in system conditions.

    """
    FULL_RANGE_S = 70
    RESET_S = 10
    CONTROL_CHECK_INTERVAL_S = 5.0 # Check every 5 seconds

    def __init__(self, name: str, services: ScadaInterface):
        super().__init__(name, services)
        self._stop_requested = False
        self.percent_keep: float = 100
        self.resetting = False
        self._movement_task = None # Track the current movement task
        self.move_start_s: float = 0
        self.latest_move_duration_s: float = 0
        # Define transitions with callback
        self.control_transitions = [
            {"trigger": "InitializationComplete", "source": "Initializing", "dest": "Dormant"},
            {"trigger": "HpTurnsOff", "source": "*", "dest": "MovingToFullSend"},
            {"trigger": "Blind", "source": "*", "dest": "MovingToFullSend"},
            {"trigger": "ReachFullSend", "source": "MovingToFullSend", "dest":"Dormant"},
            {"trigger": "HpPreparing", "source": "Dormant", "dest": "MovingToKeep"},
            {"trigger": "HpPreparing", "source": "MovingToFullSend", "dest": "MovingToKeep"},
            {"trigger": "ReachT2", "source": "MovingToKeep", "dest": "Hover"},
            {"trigger": "NeedLessKeep", "source": "Hover", "dest": "Active"},
        ]
        
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
        self.control_machine = Machine(
            model=self,
            states=SiegControlState.values(),
            transitions=self.control_transitions,
            initial=SiegControlState.Initializing,
            model_attribute="control_state",
            send_event=True,
        )
        self.control_state: SiegControlState = SiegControlState.Initializing
        self.machine = Machine(
            model=self,
            states=SiegValveState.values(),
            transitions=self.transitions,
            initial=SiegValveState.FullyKeep,
            model_attribute="valve_state",
            send_event=True, # Enable event passing to callbacks
        )
        self.valve_state: SiegValveState = SiegValveState.FullyKeep
        self.actuators_ready: bool = False
        

        # Heat pump LWT control settings
        self.target_lwt = 110.0 # Default target LWT in °F
        self.hp_boss_state = HpBossState.HpOn

        # Control parameters (match defulats in SiegLoop)
        self.proportional_gain = 2.0
        self.anticipatory_gain = 1.0
        self.anticipatory_threshold_f = 5.0
        self.min_lift_f_for_anticipation = 1.0
        self.t1 = 15 # seconds where some flow starts going through the Sieg Loop
        self.t2 = 95 # seconds where all flow starts going through the Sieg Loop
        
        self.control_interval_seconds = 5.0 

    def start(self) -> None:
        """ Required method. """
        self.services.add_task(
                asyncio.create_task(self.main(), name="Sieg Loop Synchronous Report")
            )

    def stop(self) -> None:
        """ Required method, used for stopping tasks. Noop"""
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...

    ##############################################
    # Control loop
    ##############################################

    def return_delta_percent(self) -> float:
        """Calculate delta percentage adjustment for the next 5 seconds"""
        # 1. If we don't have visiblity, trigger "Blind" which will go to FullSend
        if self.lift_f is None or self.lwt_f is None:
            self.trigger_control_event(ControlEvent.Blind)
            return 0
        
        if self.control_state not in [SiegControlState.Hover, SiegControlState.Active]:
            raise Exception(f"HUH. should not be running controlloop ")
        
        # 2. Measure the current state
        temp_diff_from_target = self.target_lwt - self.lwt_f

        # 3. Proportional control based on how far we are from target
        # If LWT is below target, increase recirculation (more keep)
        # If LWT is above target, decrease recirculation (less keep)
        percent_adjustment = self.proportional_gain * temp_diff_from_target

        # 4. Add anticipatory logic (look-ahead)
        # If approaching target quickly, start moving valve before reaching target
        if abs(temp_diff_from_target) < self.anticipatory_threshold_f and self.lift_f > self.min_lift_f_for_anticipation:
            # If approaching target fast, start opening valve early
            anticipatory_adjustment = -self.lift_f * self.anticipatory_gain  # Adjust multiplier based on testing
            percent_adjustment += anticipatory_adjustment
        
        # Calculate maximum movement possible in the control interval (physical limitation)
        max_movement = int(100 * self.CONTROL_CHECK_INTERVAL_S / self.FULL_RANGE_S)
        if percent_adjustment > 0:
            bounded_adjustment = min(percent_adjustment, max_movement)
        else:
            bounded_adjustment = max(percent_adjustment, -max_movement)

        return bounded_adjustment
    
    async def run_temperature_control(self) -> None:
        """Check current temperatures and adjust valve position if needed. Only used
        when control state is Hover (at the t2 percent where the loop is exactly keepoing
        everything) or Active"""

        #TODO think through safety to make sure it doesn't stay in 100% keep
        # if temps go away
        if self.lwt_f is None or self.ewt_f is None or self.lift_f is None:
            self.log("Missing temperature readings, skipping control adjustment")
            return

        # Calculate target percent
        delta_percent = self.return_delta_percent()
        max_movement = int(100 * self.CONTROL_CHECK_INTERVAL_S / self.FULL_RANGE_S)
        response = delta_percent/max_movement
        # If in Hover state and delta is finally negative (need less keep), 
        # transition to Active state
        if self.control_state == SiegControlState.Hover:
            if delta_percent < 0:
                self.trigger_control_event(ControlEvent.NeedLessKeep)
            else:
                self.log(f"{round(self.lwt_f,1)} [Target {round(self.target_lwt,1)}]; Lift {round(self.lift_f,1)}.")
                self.log(f"Still hovering ... waiting for delta_percent to go negative. currently {round(delta_percent,2)}")
                return
       
        self.log(f"{round(self.lwt_f,1)} [Target {round(self.target_lwt,1)}]; Lift {round(self.lift_f,1)}.  Response: {round(response * 100)}%")
        # Only move if significant change needed (avoid hunting)
        if abs(delta_percent) >= 0.5:
            # Calculate new position
            target_percent = self.percent_keep + delta_percent
            target_percent = max(0, min(100, target_percent))
            await self.prepare_new_movement_task(target_percent)


    ##############################################
    # State machine mechanics
    ##############################################

    def on_enter_moving_to_keep(self, event):
        """Called when entering the MovingToKeep state"""
        self.log(f"Moving to keep position (t2: {self.t2}%) to prepare for heat pump start")
        
        # Create a new task for the movement to t2
        asyncio.create_task(self.prepare_new_movement_task(self.t2))

    def on_enter_hover(self, event):
        """Called when entering the Hover state"""
        self.log(f"Hovering at t2 position ({self.t2}%) waiting for heat pump to establish flow")
        # We don't need to do anything special here - just wait
        # Maybe send a notification that we're hovering?
        self._send_to(
            self.hp_boss,
            SiegLoopReady()
        )

    def on_enter_dormant(self, event):
        """Called when entering the Dormant state"""
        self.log("Heat pump off, entering dormant state")

    def on_enter_active(self, event):
        ... # Nothing to do hear yet

    def on_enter_moving_to_full_send(self, event):
        self.log(f"Moving to full send")
        asyncio.create_task(self.prepare_new_movement_task(0))

        
    def trigger_control_event(self, event: ControlEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.control_state

        if self.resetting:
            raise Exception("Do not interrupt resetting to fully send or fully keep!")

        # Trigger the state machine transition
        if event == ControlEvent.HpTurnsOff:
            self.HpTurnsOff()
        elif event == ControlEvent.HpPreparing:
            self.HpPreparing()
        elif event == ControlEvent.ReachT2:
            self.ReachT2()
        elif event == ControlEvent.ReachFullSend:
            self.ReachFullSend()
        elif event == ControlEvent.NeedLessKeep:
            self.NeedLessKeep()
        elif event == ControlEvent.InitializationComplete:
            self.InitializationComplete()
        else:
            raise Exception(f"Unknown control event {event}")

        self.log(f"{event}: {orig_state} -> {self.control_state}")

        # Manually call the appropriate callback based on the new state
        if self.control_state == SiegControlState.MovingToKeep and orig_state != SiegControlState.MovingToKeep:
            self.on_enter_moving_to_keep(event)
        elif self.control_state == SiegControlState.Hover and orig_state != SiegControlState.Hover:
            self.on_enter_hover(event)
        elif self.control_state == SiegControlState.Active and orig_state != SiegControlState.Active:
            self.on_enter_active(event)
        elif self.control_state == SiegControlState.Dormant and orig_state != SiegControlState.Dormant:
            self.on_enter_dormant(event)
        elif self.control_state == SiegControlState.MovingToFullSend and orig_state != SiegControlState.MovingToFullSend:
            self.on_enter_moving_to_full_send(event)

        self._send_to(
            self.primary_scada,
            SingleMachineState(
                MachineHandle=self.node.handle,
                StateEnum=SiegControlState.enum_name(),
                State=self.control_state,
                UnixMs=now_ms,
                Cause=event
            )
        )

    ##############################################
    # Valve State Machine
    ##############################################

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

    def trigger_valve_event(self, event: ValveEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.valve_state

        if self.resetting:
            raise Exception("Do not interrupt resetting to fully send or fully keep!")

        # Trigger the state machine transition
        if event == ValveEvent.StartKeepingMore:
            self.StartKeepingMore()
        elif event == ValveEvent.StartKeepingLess:
            self.StartKeepingLess()
        elif event == ValveEvent.StopKeepingMore:
            self.StopKeepingMore()
        elif event == ValveEvent.StopKeepingLess:
            self.StopKeepingLess()
        elif event == ValveEvent.ResetToFullySend:
            self.ResetToFullySend()
        elif event == ValveEvent.ResetToFullyKeep:
            self.ResetToFullyKeep()
        else:
            raise Exception(f"Unknown valve event {event}")

        self.log(f"{event}: {orig_state} -> {self.valve_state}")

        # TODO: add a new node for the valve; sieg-loop will be control state
        # self._send_to(
        #     self.primary_scada,
        #     SingleMachineState(
        #         MachineHandle=self.node.handle,
        #         StateEnum=SiegValveState.enum_name(),
        #         State=self.valve_state,
        #         UnixMs=now_ms,
        #         Cause=event
        #     )
        # )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        from_node = self.layout.node(message.Header.Src, None)
        if from_node is None:
            return Ok(False)
        payload = message.Payload
        match payload:
            case ActuatorsReady():
                try:
                    self.process_actuators_ready(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with process_actuators_ready")
            case AnalogDispatch():
                try:
                    asyncio.create_task(self.process_analog_dispatch(from_node, payload), name="analog_dispatch")
                except Exception as e:
                    self.log(f"Trouble with process_analog_dispatch: {e}")
            case FsmFullReport():
                ... # got report back from relays
            case ResetHpKeepValue():
                try:
                    self.process_reset_hp_keep_value(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with process_reset_hp_keep_value: {e}")
            case SetLwtControlParams():
                try:
                    self.process_lwt_control_params(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with process_lwt_control_paramst: {e}")
            case SetTargetLwt():
                try:
                    self.process_set_target_lwt(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with process_set_target_lwt: {e}")
            case SiegLoopEndpointValveAdjustment():
                try:
                    asyncio.create_task(self.process_sieg_loop_endpoint_valve_adjustment(from_node, payload), name="analog_dispatch")
                except Exception as e:
                    self.log(f"Trouble withprocess_sieg_loop_endpoint_valve_adjustmen: {e}")
            case SingleMachineState():
                self.process_single_machine_state(from_node, payload)
            case _: 
                self.log(f"{self.name} received unexpected message: {message.Header}"
            )
        return Ok(True)

    def process_actuators_ready(self, from_node: ShNode, payload: ActuatorsReady) -> None:
        """Move to full send on startup"""
        self.actuators_ready = True
        asyncio.create_task(self.initialize())
        self.log(f"Actuators ready")

    async def initialize(self) -> None:
        if not self.actuators_ready:
            raise Exception("Call AFTER actuators ready")
        self.log("Initializing Sieg valve to FullySend position")
        await self.prepare_new_movement_task(0)

        # Let movement complete
        await asyncio.sleep(self.FULL_RANGE_S)

        self.log("Waiting another 5 seconds")
        await asyncio.sleep(5)
        # InitializationComplete: Initializing -> Dormant
        self.trigger_control_event(ControlEvent.InitializationComplete)
        if self.hp_boss_state in [HpBossState.PreparingToTurnOn, HpBossState.HpOn]:
            # HpPreparing: Dormant -> MovingToKeepf
            self.trigger_control_event(ControlEvent.HpPreparing)

    async def process_analog_dispatch(self, from_node: ShNode, payload: AnalogDispatch) -> None:    
        if from_node != self.boss:
            self.log(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
            return

        if self.boss.handle != payload.FromHandle:
            self.log(f"boss's handle {self.boss.handle} does not match payload FromHandle {payload.FromHandle}")
            return

        target_percent = payload.Value
        self.log(f"Received command to set valve to {target_percent}% keep")

        # move to target percent
        asyncio.create_task(self.prepare_new_movement_task(target_percent))

    def process_reset_hp_keep_value(
        self, from_node: ShNode, payload: ResetHpKeepValue
    ) -> None:
        self.log(f"Got ResetHpKeepValue")
        if from_node != self.boss:
            self.log(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
            return

        if self.boss.handle != payload.FromHandle:
            self.log(f"boss's handle {self.boss.handle} does not match payload FromHandle {payload.FromHandle}")
            return

        if payload.FromValue != self.percent_keep:
            self.send_glitch(f"Ignoring ResetHpKeepValue w FromValue {payload.FromValue} - percent keep is {self.percent_keep}")
            return
        
        if self._movement_task:
            self.send_glitch(f"Not resetting hp keep value while moving")
            return
        self.log(f"Resetting percent keep from {self.percent_keep} to {payload.ToValue} without moving valve")
        self.percent_keep = payload.ToValue
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=H0CN.hp_keep,
                Value=self.percent_keep,
                ScadaReadTimeUnixMs=int(time.time() *1000)
            )
        )

    def process_lwt_control_params(self, from_node: ShNode, payload: SetLwtControlParams) -> None:
        # consider adding to HW Layou?
        if payload.ToHandle != self.node.handle:
            self.log(f"Ignoring LwtControlParams with ToHandle {payload.ToHandle} != {self.node.handle}")
            return
        self.proportional_gain = payload.ProportionalGain
        self.anticipatory_gain = payload.AnticipatoryGain
        self.anticipatory_threshold_f = payload.AnticipatoryThresholdF
        self.min_lift_f_for_anticipation = payload.MinLiftForAnticipation
        self.t1 = payload.T1
        self.t2 = payload.T2
        self.log(f"Using {payload}")

    def process_single_machine_state(self, from_node: ShNode, payload: SingleMachineState) -> None:
        self.latest = payload
        self.log(f"JUST GOT {payload.State} from HpBoss")
        if payload.StateEnum != HpBossState.enum_name():
            raise Exception(f"Not expecting {payload}")
        if from_node != self.hp_boss:
            raise Exception("Not expecting sms except from HpBoss")
        self.hp_boss_state = payload.State
        if self.control_state == SiegControlState.Initializing:
            self.log(f"IGNORING Hp State {payload.State} until done initializing")
            return

        if payload.State == HpBossState.HpOff:
            if self.control_state not in [SiegControlState.Dormant, SiegControlState.MovingToFullSend]:
                self.trigger_control_event(ControlEvent.HpTurnsOff)
        elif payload.State == HpBossState.PreparingToTurnOn:
            if self.control_state not in [SiegControlState.Dormant, SiegControlState.MovingToFullSend]:
                self.log(f"That's strange! Got PreparingToTurnOn when control state is {self.control_state}")
            else:
                if self.is_blind:
                    self.log(f"NOT entering control loop: EWT: {self.ewt_f} LWT: {self.lwt_f}")
                else:
                    self.trigger_control_event(ControlEvent.HpPreparing)
                
    def process_set_target_lwt(self, from_node: ShNode, payload: SetTargetLwt) -> None:
        self.target_lwt = payload.TargetLwtF
        self.log(f"Target lwt is now {self.target_lwt}")

    async def process_sieg_loop_endpoint_valve_adjustment(
        self, from_node: ShNode, payload: SiegLoopEndpointValveAdjustment
    ) -> None:
        if from_node != self.boss:
            self.log(f"sieg loop expects commands from its boss {self.boss.Handle}, not {from_node.Handle}")
            return

        if self.boss.handle != payload.FromHandle:
            self.log(f"boss's handle {self.boss.handle} does not match payload FromHandle {payload.FromHandle}")
            return

        if payload.HpKeepPercent != self.percent_keep:
            self.send_glitch(f"Ignoring SiegLoopEndpointValveAdjustment w {payload.HpKeepPercent} - our keep percent is {self.percent_keep}")
            return
        if self._movement_task: 
            self.send_glitch("Ignoring SiegLoopEndpointValveAdjustment - moving already")
            return
        elif self.valve_state not in [SiegValveState.FullyKeep, SiegValveState.FullySend]:
            self.send_glitch(f"Ignoring SiegLoopEndpointValveAdjustment - percent keep at {self.percent_keep} and state {self.valve_state}")

        # Generate a new task ID for this movement
        new_task_id = str(uuid.uuid4())[-4:]
        self._current_task_id = new_task_id
        # Create a new task for the movement
        if self.valve_state == SiegValveState.FullyKeep:
            new_task = self.keep_harder(payload.Seconds, new_task_id)
            self.log(f"Keeping harder in FullyKeep state for {payload.Seconds} seconds")
        else:
            new_task = self.send_harder(payload.Seconds, new_task_id)
            self.log(f"Sending harder in {self.valve_state} state for {payload.Seconds} seconds")
        self._movement_task = asyncio.create_task(new_task) 

    async def clean_up_old_task(self) -> None:
        if hasattr(self, '_movement_task') and self._movement_task and not self._movement_task.done():
            self.log(f"Cancelling previous movement task")
            self._movement_task.cancel()
            
            # Wait for the task to actually complete
            try:
                # Use a timeout to avoid waiting forever if something goes wrong
                await asyncio.wait_for(self._movement_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                self.log("Cancelled previous task")
            
            # Ensure proper state cleanup regardless of how the task ended
            if self.valve_state == SiegValveState.KeepingMore:
                self.trigger_valve_event(ValveEvent.StopKeepingMore)
                self.log(f"Triggered StopKeepingMore after cancellation")
            elif self.valve_state == SiegValveState.KeepingLess:
                self.trigger_valve_event(ValveEvent.StopKeepingLess)
                self.log(f"Triggered StopKeepingLess after cancellation")

            # Set task to None after cancellation
            self._movement_task = None

    def complete_move(self, task_id: str) -> None:
        if self.valve_state == SiegValveState.KeepingMore:
            if self.percent_keep == 100:
                self.trigger_valve_event(ValveEvent.ResetToFullyKeep)
            else:
                self.trigger_valve_event(ValveEvent.StopKeepingMore)
        elif self.valve_state == SiegValveState.KeepingLess:
            if self.percent_keep == 0:
                self.trigger_valve_event(ValveEvent.ResetToFullySend)
            else:
                self.trigger_valve_event(ValveEvent.StopKeepingLess)
        self.log(f"Movement {task_id} completed: {self.percent_keep}%, state {self.valve_state}")

    async def prepare_new_movement_task(self, target_percent: float) -> str:
        """Create a new movement task with proper cleanup of existing tasks.
        
        Args:
            target_percent: The target valve position percentage
            
        Returns:
            task_id: The ID of the new task
        """
        # Generate a new task ID for this movement
        new_task_id = str(uuid.uuid4())[-4:]
        self._current_task_id = new_task_id
        self.log(f"Task {new_task_id}: target {target_percent}")
        
        # Cancel any existing movement task
        await self.clean_up_old_task()
        
        # Create a new task for the movement
        self._movement_task = asyncio.create_task(
            self._move_to_target_percent_keep(target_percent, new_task_id)
        )
        
        return new_task_id
    
    async def _move_to_target_percent_keep(self, target_percent: float, task_id: str) -> None:
        """Move the valve to the target percent keep value."""
        if self.percent_keep == target_percent:
            self.log(f"Already at target {round(target_percent,2)}%")
            # Check if we need to trigger ReachT2 event
            if self.control_state == SiegControlState.MovingToKeep and target_percent == self.t2:
                self.trigger_control_event(ControlEvent.ReachT2)
            elif self.control_state == SiegControlState.MovingToFullSend and target_percent == 0:
                    self.trigger_control_event(ControlEvent.ReachFullSend)
            return
            
        # Determine direction
        moving_to_more_keep = self.percent_keep < target_percent
    
        # Wait a moment to ensure the state machine has settled
        await asyncio.sleep(0.2)
        self.log(f"{round(self.percent_keep)} keep [{task_id} MOVE TO {round(target_percent)}% STARTING]")
        # Set the appropriate state
        try:
            if moving_to_more_keep:
                self.log(f"Starting movement to MORE keep ({self.percent_keep}% -> {target_percent}%)")
                self.trigger_valve_event(ValveEvent.StartKeepingMore)
                # Now process the movement in a loop
                while self.percent_keep < target_percent:
                    # Check if this task has been superseded
                    if task_id != self._current_task_id:
                        self.log(f"Task {task_id} has been superseded, stopping")
                        break
                    delta_percent = target_percent - self.percent_keep 
                    if delta_percent < 1:
                        # keep a fraction of a percent
                        await self._keep_one_percent_more(task_id, delta_percent)
                    else:
                        await self._keep_one_percent_more(task_id)
                    await self._keep_one_percent_more(task_id)
                    # Allow for cancellation to be processed
                    await asyncio.sleep(0)
            else:
                self.log(f"Starting movement to LESS keep ({self.percent_keep}% -> {target_percent}%)")
                self.trigger_valve_event(ValveEvent.StartKeepingLess)
                
                # Now process the movement in a loop
                while self.percent_keep > target_percent:
                    # Check if this task has been superseded
                    if task_id != self._current_task_id:
                        self.log(f"Task {task_id} has been superseded, stopping")
                        break
                        
                    delta_percent =  self.percent_keep  - target_percent
                    if delta_percent < 1:
                        # keep a fraction of a percent less
                        await self._keep_one_percent_less(task_id, delta_percent)
                    else:
                        await self._keep_one_percent_less(task_id)
                    # Allow for cancellation to be processed
                    await asyncio.sleep(0)

            # At the end of the method, after movement is complete:
            if task_id == self._current_task_id:
                self.log(f"{round(self.percent_keep)} keep [{task_id} COMPLETED]")
                self.complete_move(task_id)
                
                # Check if we need to trigger ReachT2 event
                if self.control_state == SiegControlState.MovingToKeep and target_percent == self.t2:
                    self.trigger_control_event(ControlEvent.ReachT2)
                # Check if we need to trigger ReachFullSend event
                elif self.control_state == SiegControlState.MovingToFullSend and target_percent == 0:
                    self.trigger_control_event(ControlEvent.ReachFullSend)

        except asyncio.CancelledError:
            self.log(f"Movement cancelled at {self.percent_keep}%")
            # Let the cancellation propagate to the caller - don't set state here
            # as clean_up_old_task handles the FSM state transition
            raise
        
        except Exception as e:
            self.log(f"Error during movement: {e}")
            self.complete_move(task_id)

        finally:
            # Always set the task to None when complete, whether successful or not
            self._movement_task = None

    async def _keep_one_percent_less(self, task_id: str, fraction: Optional[float] = None) -> None:
        """Or keep fraction percent less ... REQUIRES fraction to be less than 1"""
        # Check if we're still the current task
        if task_id != self._current_task_id:
            return
        if self.valve_state != SiegValveState.KeepingLess:
            raise Exception(f"Only call _keep_one_percent_less in state KeepingLess, not {self.valve_state}")
        percent = 1
        if fraction:
            if fraction > 1:
                raise Exception("fraction needs to be less than 1")
            percent = fraction
        sleep_s = percent * self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)

        # Check again if we're still the current task after sleeping
        if task_id != self._current_task_id:
            return
        
        self.percent_keep = orig_keep - percent
        # self.log(f"{self.percent_keep}% keep [{task_id}]")
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=H0CN.hp_keep,
                Value=round(self.percent_keep),
                ScadaReadTimeUnixMs=int(time.time() *1000)
            )
        )

    async def _keep_one_percent_more(self, task_id: str, fraction: Optional[float] = None) -> None:
        """Or keep fraction percent more ... REQUIRES fraction to be less than 1"""
        # Check if we're still the current task
        if task_id != self._current_task_id:
            return
        if self.valve_state != SiegValveState.KeepingMore:
            raise Exception(f"Only call _keep_one_percent_more in state KeepingMore, not {self.valve_state}")
        percent = 1
        if fraction:
            if fraction > 1:
                raise Exception("fraction needs to be less than 1")
            percent = fraction
        sleep_s = percent * self.FULL_RANGE_S / 100
        orig_keep = self.percent_keep
        await asyncio.sleep(sleep_s)

        # Check again if we're still the current task after sleeping
        if task_id != self._current_task_id:
            return
        
        self.percent_keep = orig_keep + percent
        # self.log(f"{self.percent_keep}% keep [{task_id}]")
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=H0CN.hp_keep,
                Value=round(self.percent_keep),
                ScadaReadTimeUnixMs=int(time.time() *1000)
            )
        )

    async def keep_harder(self, seconds: int, task_id: str) -> None:
        try:
            if self.valve_state != SiegValveState.FullyKeep:
                self.log("Use only when in FullyKeep")
                return
            self.change_to_hp_keep_more()
            self.sieg_valve_active()
            self.send_glitch(f"[{task_id}] Keeping for {seconds} seconds more")
            await asyncio.sleep(seconds)
            # Check if this task has been superseded
            if task_id != self._current_task_id:
                self.log(f"Task {task_id} has been superseded!")
            else:
                self.sieg_valve_dormant()
                
        except asyncio.CancelledError:
            self.log(f"send_harder task cancelled")
            # Don't set valve to dormant - the cancelling code handles this
            raise
        except Exception as e:
            self.log(f"Error during keep_harder: {e}")
            self.sieg_valve_dormant()
            self.send_glitch(f"Error during keep_harder: {e}", LogLevel.Error)
        finally:
            # Always set the task to None when complete
            self._movement_task = None
            self.log(f"Task {task_id} complete")

    async def send_harder(self, seconds: int, task_id: str) -> None:
        try:
            if self.valve_state != SiegValveState.FullySend:
                self.log("Use when in FullySend")
                return
            self.change_to_hp_keep_less()
            self.sieg_valve_active()
            self.send_glitch(f"[{task_id}] Sending for {seconds} seconds more")
            await asyncio.sleep(seconds)
            # Check if this task has been superseded
            if task_id != self._current_task_id:
                self.log(f"Task {task_id} has been superseded!")
            else:
                self.sieg_valve_dormant()
        except asyncio.CancelledError:
            self.log(f"keep_harder task cancelled")
            # Don't set valve to dormant - the cancelling code handles this
            raise
        except Exception as e:
            self.log(f"Error during send_harder: {e}")
            self.sieg_valve_dormant()
            self.send_glitch(f"Error during send_harder: {e}", LogLevel.Error)
        finally:
            # Always set the task to None when complete
            self._movement_task = None
            self.log(f"Task {task_id} complete")

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, 400)]
    
    async def main(self):
        # This loop happens either every flatline_seconds or every second
        while not self._stop_requested:
            now = datetime.now()
            # Determine if we're at the top of a 5-second interval
            seconds_into_5s = now.second % 5
            milliseconds = now.microsecond / 1000

            if seconds_into_5s == 0 and milliseconds < 100:
                # We're at the top of a 5-second interval (within 100ms)
                if not self.is_blind() \
                    and self.control_state in [SiegControlState.Hover, SiegControlState.Active]:
                    # Run temperature control without awaiting to avoid blocking
                    asyncio.create_task(self.run_temperature_control())
        
            next_second = 1.0 - (now.microsecond / 1_000_000)
            await asyncio.sleep(next_second)

            # Report status periodically
            if now.second == 0 and now.minute % 5 == 0:
                self._send(PatInternalWatchdogMessage(src=self.name))
                self._send_to(
                self.primary_scada,
                    SingleReading(
                        ChannelName=H0CN.hp_keep,
                        Value=round(self.percent_keep),
                        ScadaReadTimeUnixMs=int(time.time() *1000)
                    )
                )
            
    def send_glitch(self, summary: str, log_level: LogLevel=LogLevel.Info) -> None:
        self._send_to(
                self.primary_scada,
                Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=log_level,
                    Summary=summary,
                    Details=summary
                )
            )
        self.log(summary)

    @property
    def lwt_f(self) -> Optional[float]:
        current_lwt = self.scada_services.data.latest_channel_values.get(H0CN.hp_lwt)
        if current_lwt is None:
            return None
        return self.to_fahrenheit(current_lwt / 1000)

    @property
    def ewt_f(self) -> Optional[float]:
        current_lwt = self.scada_services.data.latest_channel_values.get(H0CN.hp_ewt)
        if current_lwt is None:
            return None
        return self.to_fahrenheit(current_lwt / 1000)

    @property
    def lift_f(self) -> Optional[float]:
        """ The lift of the heat pump: leaving water temp minus entering water temp.
        Returns 0 if this is negative (e.g. during defrost). Returns None if missing 
        a key temp. 
        """
        if self.lwt_f is None:
            return None
        if self.ewt_f is None:
            return None
        lift_f = max(0, self.lwt_f - self.ewt_f)
        return lift_f

    def is_blind(self) -> bool:
        if self.lift_f is None:
            return True
        return False