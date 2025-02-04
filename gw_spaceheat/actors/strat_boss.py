import asyncio
import time
import uuid
from collections import deque
from typing import Optional,  Sequence
from data_classes.house_0_names import H0CN, H0N
from gwproactor.message import Message, PatInternalWatchdogMessage
from gwproactor import MonitoredName, ServicesInterface
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName
from gwproto.named_types import AnalogDispatch, FsmFullReport
from result import Result

from actors.scada_actor import ScadaActor
from enums import HpOnOff, HpModel, StratBossEvent, StratBossState
from named_types import FsmEvent, StratBossReady, StratBossTrigger
from transitions import Machine





class StratBoss(ScadaActor):
    """Protects thermal stratification during heat pump transitions

    This actor manages system behavior during heat pump startup and defrost cycles to preserve
    valuable thermal stratification in storage and buffer tanks. It operates as part of the
    hierarchical state machine system with two states:

    - Dormant: Default state when stratification protection is not needed
    - Active: Actively managing relays & 010V actuators to protect stratification

    The actor is activated by either:
    1. Detection of heat pump defrost cycles through power and temperature patterns
    2. Receipt of HpTurningOn messages during heat pump startup

    When activated, it:
    1. Triggers its parent node to enter a stratification protection state 
    2. Takes control of the store charge/discharge relay and thermostat relays
    3. Configures the system to circulate through distribution rather than storage or buffer
    4. Maintains this configuration until
        - heat pump normalizes (as detected by a reasonable lift), or
        - HpTurningOff message received, or
        - the Distribution Pump fails (pump doctor takes over), or
        - A longish timer times out (e.g. ~12 minutes)

    This helps prevent mixing of stratified layers during periods when the heat pump is 
    circulating water but not actively heating it. Since this is a hydronic system it does
    not annoy residents the way blowing cold air does in defrost for air-to-air HPs - the
    circulating water is likely still above room temperature, just not enough to actively heat.

    Attributes:
        state (StratificationManagerState): Current state (Dormant or Active)
        parent_node (ShNode): Current parent node (home_alone or atomic_ally)
        my_relays (List[ShNode]): Relays under control when Active
    """
    TIMEOUT_MINUTES = 3
    
    DIST_PUMP_ON_SECONDS = 45 # time it takes to get the distributin pump on when its off
    VALVED_TO_DISCHARGE_SECONDS = 30 # time it takes to go from valve in charge -> valve in discharge
    LG_HYDROKIT_PRIMARY_PUMP_DELAY_SECONDS = 120 # TODO: move into hardware layout
    SAMSUNG_HYDROKIT_PRIMARY_PUMP_DELAY_SECONDS = 0
    DEFROST_DETECT_SLEEP_S = 2 # for the strat watcher as it tracks
    LIFT_DETECT_SLEEP_S = 5
    HP_LIFT_DEG_F = 4
    WATCHDOG_PAT_S = 60

    states = StratBossState.values()

    transitions = [
        # Dormant -> Active triggers
        {"trigger": "HpTurnOnReceived", "source": "Dormant", "dest": "Active"},
        {"trigger": "DefrostDetected", "source": "Dormant", "dest": "Active"},
        # Active -> Dormant triggers
        {"trigger": "LiftDetected", "source": "Active", "dest": "Dormant"},
        {"trigger": "HpTurnOffReceived", "source": "Active", "dest": "Dormant"},
        {"trigger": "Timeout", "source": "Active", "dest": "Dormant"},
        {"trigger": "BossCancels", "source": "Active", "dest": "Dormant"},
    ]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False
        self.hp_model = self.settings.hp_model # TODO: will move to hardware layout
        self.primary_pump_delay_seconds: int = self.get_primary_pump_delay_seconds()
        self.state: StratBossState = StratBossState.Dormant
        self.machine = Machine(
            model=self,
            states=StratBoss.states,
            transitions=StratBoss.transitions,
            initial=StratBossState.Dormant,
            send_event=False
        )
        self.idu_w_readings = deque(maxlen=5)
        self.odu_w_readings = deque(maxlen=5)
        self.log("STRAT BOSS DONE INITIALIZING")

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(
                self.defrost_watcher(), name="defrost_watcher"
            )
        )

    def stop(self) -> None:
        """ Required method, used for stopping tasks. Noop"""
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...


    def sidelined(self) -> bool:
        """ Sidelined if it is out of the chain of command; e.g boss is own ShNode"""
        if self.boss == self.node:  # not in the command tree
            return True
        return False

    def get_primary_pump_delay_seconds(self) -> int:
        """Seconds between closing the HpOps relay and primary pump coming on
        """
        if self.hp_model == HpModel.SamsungHighTempHydroKitPlusMultiV:
            return self.SAMSUNG_HYDROKIT_PRIMARY_PUMP_DELAY_SECONDS
        elif self.hp_model == HpModel.LgHighTempHydroKitPlusMultiV:
            return self.LG_HYDROKIT_PRIMARY_PUMP_DELAY_SECONDS
        else:
            raise Exception(f"Don't have primary pump delay seconds for {self.hp_model}!")

    def strat_prep_seconds(self) -> int:
        """
        Seconds required before Charge/Discharge valved to discharge and dist pump on full
        """
        # TODO: check current valve and pump state first
        return max(self.DIST_PUMP_ON_SECONDS, self.VALVED_TO_DISCHARGE_SECONDS)

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if self.sidelined():
            self.log(f"Sidelined so ignoring messages! Handle: {self.node.handle}")
            return

        from_node = self.layout.node(message.Header.Src, None)
        if from_node is None:
            return

        payload = message.Payload
        match payload:
            case FsmEvent():
                try:
                    self.fsm_event_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with fsm_event_received: {e}")
            case FsmFullReport():
                ... # direct reports following up re acting on commands given
            case StratBossTrigger():
                self.strat_boss_trigger_received(from_node, payload)
            case _: 
                self.log(f"{self.name} received unexpected message: {message.Header}"
            )

    def fsm_event_received(self, from_node: ShNode, payload: FsmEvent) -> None:
        if from_node != self.hp_relay_boss:
            self.log(f"Rejecting FsmEvent. Expected from_node hp_relay_boss but got {from_node.Name}")
        if payload.ToHandle != self.hp_relay_boss.Handle:
            self.log(f"Rejecting FsmEvent. Excected ToHandle {self.hp_relay_boss.Handle:} but got {payload.ToHandle}")
        if payload.EventType == HpOnOff.enum_name():
            let_boss_know = False
            if payload.EventName == HpOnOff.TurnOn and self.state == StratBossState.Dormant:
                let_boss_know = True
                trigger = StratBossTrigger(
                    FromState=StratBossState.Dormant,
                    ToState=StratBossState.Active,
                    Trigger=StratBossEvent.HpTurnOnReceived
                )
            elif payload.EventName == HpOnOff.TurnOff and self.state == StratBossState.Active:
                let_boss_know = True
                trigger = StratBossTrigger(
                    FromState=StratBossState.Active,
                    ToState=StratBossState.Dormant,
                    Trigger=StratBossEvent.HpTurnOffReceived,
                )
            if let_boss_know:
                self._send_to(self.boss, trigger)

    def strat_boss_trigger_received(self, from_node: ShNode, payload: StratBossTrigger):
        """
        Receiving this message from the boss means the command tree reflects ToState
        """
        self.log("Got StratBossTrigger")
        if self.boss != from_node:
            self.log(f"Ignoring trigger from {from_node.handle}. My handle is {self.node.handle}") # todo: send glitch
            return
        if payload.FromState != self.state:
            self.log(f"Ignoring trigger. payload.FromState {payload.FromState} and self.state {self.state}")
            return
        self.pull_trigger(payload)
        
        if payload.Trigger == StratBossEvent.HpTurnOnReceived:
            if self.strat_prep_seconds() > self.primary_pump_delay_seconds:
                asyncio.create_task(self._wait_to_close_hp_relay())

    def pull_trigger(self, trigger: StratBossTrigger):
        if trigger.FromState != self.state:
            return
        
        before = self.state
        if trigger.Trigger == StratBossEvent.HpTurnOnReceived:
            self.HpTurnOnReceived()
        elif trigger.Trigger == StratBossEvent.DefrostDetected:
            self.DefrostDetected()
        elif trigger.Trigger == StratBossEvent.LiftDetected:
            self.LiftDetected()
        elif trigger.Trigger == StratBossEvent.HpTurnOffReceived:
            self.HpTurnOffReceived()
        elif trigger.Trigger == StratBossEvent.Timeout:
            self.Timeout()
        elif trigger.Trigger == StratBossEvent.BossCancels:
            self.BossCancels()
        else:
            self.log(f"DON'T KNOW TRIGGER {trigger.Trigger}") # TODO: add Glitch
        self.log(f"{trigger.Trigger}: {before} -> {self.state}")
        if self.state == StratBossState.Active:
            asyncio.create_task(self._timeout_timer())
            asyncio.create_task(self.active(trigger.Trigger))

    def turn_on_dist_pump(self) -> None:
        """
        Turn on heat calls for all zones and set 010V for dist pump to 100
        """
        # start heat calls on all white wires
        for zone in self.layout.zone_list:
            self.heatcall_ctrl_to_scada(zone)
            self.stat_ops_close_relay(zone)
        # caleffi zone valve controller takes about 30 seconds CHECK
        dist_010v_node = self.layout.node(H0N.dist_010v)
        # set 010V output to 100
        self._send_to(
            dist_010v_node,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=dist_010v_node.handle,
                AboutName=dist_010v_node.Name,
                Value=100,
                TriggerId=str(uuid.uuid4()),
                UnixTimeMs=int(time.time() * 1000),
            )
        )
        self.log(f"Sent analog dispatch to {dist_010v_node.handle}")

    async def active(self, trigger: StratBossEvent) -> None:
        if trigger == StratBossEvent.HpTurnOnReceived:
            max_strat_prep_seconds = max(self.DIST_PUMP_ON_SECONDS, self.VALVED_TO_DISCHARGE_SECONDS)
            wait_s = self.primary_pump_delay_seconds - max_strat_prep_seconds # could be ~75 s for LG
            if wait_s > 5:
                wait_s = wait_s - 5
                self.log(f"primary on in {self.primary_pump_delay_seconds} and my max prep is {max_strat_prep_seconds}")
                self.log(f"Waiting {wait_s} before changing relays")
                await asyncio.sleep(wait_s)
        asyncio.create_task(self._lift_timer())
        #Make sure we're still active before proceeding in case we waited.
        if self.state == StratBossState.Active:
            self.valved_to_discharge_store()
            self.turn_on_dist_pump()
            # while self.state == StratBossState.Active:
            #     await asyncio.sleep(self.SLEEP_LOOP_S) # Add PID control of dist pump 010 to match dist flow to primary flow

    async def _wait_to_close_hp_relay(self) -> None:
        wait_seconds = max(0, self.primary_pump_delay_seconds - self.strat_prep_seconds())
        self.log(f"Pump delay seconds {self.primary_pump_delay_seconds} and strat prep seconds {self.strat_prep_seconds()}. Sleeping {wait_seconds}")
        await asyncio.sleep(wait_seconds)
        self._send_to(self.hp_relay_boss, StratBossReady())

    async def _lift_timer(self) -> None:
        """ Wait 2 minutes. Then if LWT - EWT > 4 F, send trigger"""
        self.log("sleeping for 2 minutes before attempting to detect lift")
        await asyncio.sleep(2*60)
        while self.state == StratBossState.Active:
            if self.latest_lift_f():
                self.log(f"Latest lift is {self.latest_lift_f()}")
                if self.latest_lift_f() > self.HP_LIFT_DEG_F:
                    self._send_to(self.boss,StratBossTrigger(
                        FromState=StratBossState.Active,
                        ToState=StratBossState.Dormant,
                        Trigger=StratBossEvent.LiftDetected
                    ))
            else:
                self.log("No data from ewt and/or lwt! So no lift detected")
            await asyncio.sleep(self.LIFT_DETECT_SLEEP_S)
                
    
    async def _timeout_timer(self) -> None:
        """ Wait 12 minutes. If still active at the end then pull the ActiveTwelveMinutes Trigger"""
        self.log(f"Waiting {self.TIMEOUT_MINUTES} minutes and then timing out if still active")
        await asyncio.sleep(self.TIMEOUT_MINUTES * 60)
        if self.state == StratBossState.Active:
            self.log("Letting boss know its time to go dormant")
            self._send_to(self.boss, StratBossTrigger(
                FromState=StratBossState.Active,
                ToState=StratBossState.Dormant,
                Trigger=StratBossEvent.Timeout
            ))
    
    
    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.WATCHDOG_PAT_S * 2.1)]

    async def defrost_watcher(self) -> None:
        """
        Responsible for helping to detect and triggering the defrost state change
        """
        self.log("RUNNING THE DEFROST WATCHER HERE ")
        self.last_pat_s = 0
        odu_pwr_channel = self.layout.channel(H0CN.hp_odu_pwr)
        idu_pwr_channel = self.layout.channel(H0CN.hp_idu_pwr)
        assert odu_pwr_channel.TelemetryName == TelemetryName.PowerW
        while not self._stop_requested:
            if time.time() - self.last_pat_s > self.WATCHDOG_PAT_S:
                self.log("patting watchdog")
                self._send(PatInternalWatchdogMessage(src=self.name))
                self.last_pat_s = time.time()
            if odu_pwr_channel in self.data.latest_channel_values and idu_pwr_channel in self.data.latest_channel_values:
                odu_pwr = self.data.latest_channel_values[odu_pwr_channel]
                idu_pwr = self.data.latest_channel_values[idu_pwr_channel]
                self.odu_w_readings.append(odu_pwr)
                self.idu_w_readings.append(idu_pwr)
                if self.state == StratBossState.Dormant:
                    if self.hp_model == HpModel.LgHighTempHydroKitPlusMultiV:
                        if self.lg_high_temp_hydrokit_entering_defrost():
                            self._send_to(self.boss, StratBossTrigger(
                                    FromState=StratBossState.Dormant,
                                    ToState=StratBossState.Active,
                                    Trigger=StratBossEvent.DefrostDetected
                                ) 
                            )
                    if self.hp_model == HpModel.SamsungHighTempHydroKitPlusMultiV:
                        if self.samsung_high_temp_hydrokit_entering_defrost():
                            self._send_to(self.boss, StratBossTrigger(
                                FromState=StratBossState.Dormant,
                                    ToState=StratBossState.Active,
                                    Trigger=StratBossEvent.DefrostDetected
                                )
                            )
            await asyncio.sleep(self.DEFROST_DETECT_SLEEP_S)

    def lg_high_temp_hydrokit_entering_defrost(self) -> bool:
        """
        The Lg High Temp Hydrokit is entering defrost if:  
          - Indoor Unit Power > Outdoor Unit Power and
          - IDU Power going up and
          - ODU power going down
        """
        entering_defrost = True
        if self.odu_w_readings[-1] > self.idu_w_readings[-1]:
            entering_defrost = False
        elif self.idu_w_readings[-1] < self.idu_w_readings[0]: # idu going down
            entering_defrost = False
        elif self.odu_w_readings[-1] > self.odu_w_readings[0]: # odu going up
            entering_defrost = False
        return entering_defrost
    
    def samsung_high_temp_hydrokit_entering_defrost(self) -> bool:
        """
        The Samsung High Temp Hydrokit is entering defrost if:  
          - IDU Power  - ODU Power > 1500
          - ODU Power < 500
        """
        entering_defrost = True
        if self.idu_w_readings[-1] - self.odu_w_readings[-1] < 1500:
            entering_defrost = False
        elif self.odu_w_readings > 500:
            entering_defrost = False
        return entering_defrost

    def latest_lift_f(self) -> Optional[float]:
        ewt_channel = self.layout.channel(H0CN.hp_ewt)
        lwt_channel = self.layout.channel(H0CN.hp_lwt)
         # TODO: add these channels to the test objects!
        if ewt_channel is None:
            return None
        assert ewt_channel.TelemetryName == TelemetryName.WaterTempCTimes1000
        assert lwt_channel.TelemetryName == TelemetryName.WaterTempCTimes1000
        if ewt_channel.Name not in self.data.latest_channel_values:
            return None
        if lwt_channel.Name not in self.data.latest_channel_values:
            return None
        ewt_f = c_to_f(self.data.latest_channel_values[ewt_channel.Name] / 1000)
        lwt_f = c_to_f(self.data.latest_channel_values[ewt_channel.Name] / 1000)
        return lwt_f - ewt_f


def c_to_f(temp_c: float) -> float:
    return 32 + 8*temp_c/5

