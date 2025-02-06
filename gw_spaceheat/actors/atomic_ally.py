import asyncio
import time
import uuid
from enum import auto
from typing import cast, List, Sequence, Optional
from datetime import datetime

import pytz
from data_classes.house_0_names import H0CN, H0N
from gw.enums import GwStrEnum
from gwproactor import MonitoredName, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.components.dfr_component import DfrComponent

from gwproto.enums import ActorClass, FsmReportType
from gwproto.named_types import (AnalogDispatch, FsmAtomicReport, FsmFullReport,
                                 MachineStates)
from result import Ok, Result
from transitions import Machine

from actors.scada_actor import ScadaActor
from actors.scada_data import ScadaData
from enums import LogLevel, StratBossState, StratBossEvent
from named_types import (
    AllyGivesUp, EnergyInstruction, Glitch, GoDormant,
    Ha1Params, HeatingForecast, RemainingElec, SuitUp, WakeUp, HackOilOn, HackOilOff, StratBossTrigger, NewCommandTree
)


class AtomicAllyState(GwStrEnum):
    Dormant = auto()
    WaitingElec = auto()
    WaitingNoElec = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()
    HpOffOilBoilerTankAquastat = auto()
    StratBoss = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "atomic.ally.state"


class AtomicAllyEvent(GwStrEnum):
    NoMoreElec = auto()
    ElecAvailable = auto()
    ElecBufferFull = auto()
    ElecBufferEmpty = auto()
    NoElecBufferFull = auto()
    NoElecBufferEmpty = auto()
    WakeUp = auto()
    GoDormant = auto()
    StartHackOil = auto()
    StopHackOil = auto()
    StartStratSaving = auto()
    StopStratSaving = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "atomic.ally.event"


class AtomicAlly(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60

    states = [
        AtomicAllyState.Dormant.value,
        AtomicAllyState.WaitingElec.value,
        AtomicAllyState.WaitingNoElec.value,
        AtomicAllyState.HpOnStoreOff.value,
        AtomicAllyState.HpOnStoreCharge.value,
        AtomicAllyState.HpOffStoreOff.value,
        AtomicAllyState.HpOffStoreDischarge.value,
        AtomicAllyState.HpOffOilBoilerTankAquastat.value,
        AtomicAllyState.StratBoss.value,


    ]

    transitions = (
        [
        # Waiting for temperatures, no electricity left
        {"trigger": "ElecAvailable", "source": "WaitingNoElec", "dest": "WaitingElec"},
        {"trigger": "NoElecBufferEmpty", "source": "WaitingNoElec", "dest": "HpOffStoreDischarge"},
        {"trigger": "NoElecBufferFull", "source": "WaitingNoElec", "dest": "HpOffStoreOff"},
        {"trigger": "ElecBufferEmpty", "source": "WaitingNoElec", "dest": "HpOnStoreOff"},
        {"trigger": "ElecBufferFull", "source": "WaitingNoElec", "dest": "HpOnStoreCharge"},
        # Waiting for temperatures, electricity available
        {"trigger": "NoMoreElec", "source": "WaitingElec", "dest": "WaitingNoElec"},
        {"trigger": "NoElecBufferEmpty", "source": "WaitingElec", "dest": "HpOffStoreDischarge"},
        {"trigger": "NoElecBufferFull", "source": "WaitingElec", "dest": "HpOffStoreOff"},
        {"trigger": "ElecBufferEmpty", "source": "WaitingElec", "dest": "HpOnStoreOff"},
        {"trigger": "ElecBufferFull", "source": "WaitingElec", "dest": "HpOnStoreCharge"},
        # 1 Starting at: HP on, Store off ============= HP -> buffer
        {"trigger": "ElecBufferFull", "source": "HpOnStoreOff", "dest": "HpOnStoreCharge"},
        {"trigger": "NoMoreElec", "source": "HpOnStoreOff", "dest": "HpOffStoreOff"},
        # 2 Starting at: HP on, Store charging ======== HP -> storage
        {"trigger": "ElecBufferEmpty", "source": "HpOnStoreCharge", "dest": "HpOnStoreOff"},
        {"trigger": "NoMoreElec", "source": "HpOnStoreCharge", "dest": "HpOffStoreOff"},
        # 3 Starting at: HP off, Store off ============ idle
        {"trigger": "NoElecBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOffStoreDischarge"},
        {"trigger": "ElecBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOnStoreOff"},
        {"trigger": "ElecBufferFull", "source": "HpOffStoreOff", "dest": "HpOnStoreCharge"},
        # 4 Starting at: Hp off, Store discharging ==== Storage -> buffer
        {"trigger": "NoElecBufferFull", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
        {"trigger": "ElecBufferEmpty", "source": "HpOffStoreDischarge", "dest": "HpOnStoreOff"},
        {"trigger": "ElecBufferFull", "source": "HpOffStoreDischarge", "dest": "HpOnStoreCharge"},
        # 5 Oil boiler on during onpeak
    ] + [
        {"trigger": "StartHackOil", "source": state, "dest": "HpOffOilBoilerTankAquastat"}
        for state in states if state not in  ["Dormant", "HpOffOilBoilerTankAquastat"]
    ] + [
        {"trigger":"StopHackOil", "source": "HpOffOilBoilerTankAquastat", "dest": "WaitingNoElec"}
        # Going dormant and waking up
    ] + [
        {"trigger": "GoDormant", "source": state, "dest": "Dormant"} for state in states if state != "Dormant"
    ] + [
        {"trigger":"WakeUp", "source": "Dormant", "dest": "WaitingNoElec"}
    ] + [
            {"trigger": "StartStratSaving", "source": state, "dest": "StratBoss"}
            for state in states if state not in ["Dormant", "StratBoss"]
    ] + [{"trigger":"StopStratSaving", "source": "StratBoss", "dest": "WaitingNoElec"}]
    )

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False
        # Temperatures
        self.cn: H0CN = self.layout.channel_names
        self.temperature_channel_names = [
            H0CN.buffer.depth1, H0CN.buffer.depth2, H0CN.buffer.depth3, H0CN.buffer.depth4,
            H0CN.hp_ewt, H0CN.hp_lwt, H0CN.dist_swt, H0CN.dist_rwt, 
            H0CN.buffer_cold_pipe, H0CN.buffer_hot_pipe, H0CN.store_cold_pipe, H0CN.store_hot_pipe,
            *(depth for tank in self.cn.tank.values() for depth in [tank.depth1, tank.depth2, tank.depth3, tank.depth4])
        ]
        self.temperatures_available = False
        # State machine
        self.machine = Machine(
            model=self,
            states=AtomicAlly.states,
            transitions=AtomicAlly.transitions,
            initial=AtomicAllyState.Dormant,
            send_event=True,
        )     
        self.state: AtomicAllyState = AtomicAllyState.Dormant 
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.is_simulated = self.settings.is_simulated
        self.log(f"Params: {self.params}")
        self.log(f"self.is_simulated: {self.is_simulated}")
        self.forecasts: HeatingForecast = None
        self.remaining_elec_wh = None
        self.storage_declared_full = False
        self.storage_full_since = time.time()
        if H0N.atomic_ally not in self.layout.nodes:
            raise Exception(f"AtomicAlly requires {H0N.atomic_ally} node!!")
        self.set_normal_command_tree()
        self.cancel_strat_boss()
    
    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="AtomicAlly keepalive")
        )

    def stop(self) -> None:
        self._stop_requested = True
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        from_node = self.layout.node(message.Header.Src, None)
        match message.Payload:
            case EnergyInstruction():
                self.log(f"Received an EnergyInstruction for {message.Payload.AvgPowerWatts} Watts average power")
                self.remaining_elec_wh = message.Payload.AvgPowerWatts
                self.engage_brain()
            case GoDormant():
                if self.state != AtomicAllyState.Dormant.value:
                    # GoDormant: AnyOther -> Dormant ...
                    self.trigger_event(AtomicAllyEvent.GoDormant)
                    self.log("Going dormant")
            case HackOilOn():
                if not self.settings.fuel_substitution:
                    self.log("Ignoring HackOilOn message since fuel substitution is not activated")
                elif self.state not in (AtomicAllyState.HpOffOilBoilerTankAquastat, AtomicAllyState.Dormant):
                    self.log("Acting on hack.oil.on message")
                    previous_state = self.state
                    self.trigger_event(AtomicAllyEvent.StartHackOil)
                    self.update_relays(previous_state)
                else:
                    self.log(f"Received hack.oil.on. In state {self.state} so ignoring")
            case HackOilOff():
                if self.state == AtomicAllyState.HpOffOilBoilerTankAquastat:
                    self.log("Acting on hack.oil.off message")
                    self.trigger_event(AtomicAllyEvent.StopHackOil)
                    self.update_relays(AtomicAllyState.HpOffOilBoilerTankAquastat)
                else:
                    self.log(f"Received hack.oil.off. In state {self.state} so ignoring ")
            case RemainingElec():
                # TODO: perhaps 1 Wh is not the best number here
                if message.Payload.RemainingWattHours <= 1:
                    if "HpOn" in self.state and datetime.now(self.timezone).minute<55:
                        self.trigger_event(AtomicAllyEvent.NoMoreElec)
                self.remaining_elec_wh = message.Payload.RemainingWattHours
            case WakeUp():
                if self.state == AtomicAllyState.Dormant.value:
                    self.set_normal_command_tree() 
                    self.cancel_strat_boss()
                    self.suit_up()
            case HeatingForecast():
                self.log("Received forecast")
                self.forecasts: HeatingForecast = message.Payload
            case StratBossTrigger():
                try:
                    self.strat_boss_trigger_received(from_node, message.Payload)
                except Exception as e:
                    self.log(f"Problem strat_bss_trigger_received: {e}")

        return Ok(True)
    
    def strat_boss_trigger_received(self, from_node: Optional[ShNode], payload: StratBossTrigger) -> None:
        self.log("Strat boss trigger received!")
        if self.state == AtomicAllyState.Dormant:
            self.log(f"state is {self.state}")
            self.log("strat boss should be sidelined and NOT sending messages but strat_boss_trigger_received. IGNORING")
            return
        
        if payload.FromState == StratBossState.Dormant:
            if self.state == AtomicAllyState.StratBoss:
                raise Exception("Inconsistency! StratBoss thinks its Dormant but AA is in StratBoss State")
            self.set_strat_saver_command_tree()
            self.trigger_event(AtomicAllyEvent.StartStratSaving)
            # confirm change of command tree by returning payload to strat boss
            self._send_to(dst=self.strat_boss, payload=payload)
        else: 
            if self.state != AtomicAllyState.StratBoss:
                raise Exception("Inconsistency! StratBoss thinks its Active but HA is not in StratBoss State")
            self.set_normal_command_tree()
            self.trigger_event(AtomicAllyEvent.StopStratSaving)
            self.initialize_actuators()
            self.engage_brain()
            # confirm change of command tree by returning payload to strat boss
            self._send_to(dst=self.strat_boss, payload=payload)

    def set_normal_command_tree(self) -> None:

        hp_relay_boss = self.layout.node(H0N.hp_relay_boss)
        hp_relay_boss.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{hp_relay_boss.Name}"
        
        strat_boss = self.layout.node(H0N.strat_boss)
        strat_boss.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{strat_boss.Name}"


        for node in self.my_actuators():
            if node.Name == H0N.hp_scada_ops_relay:
                node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{hp_relay_boss.Name}.{node.Name}"
            else:
                node.Handle =  f"{H0N.atn}.{H0N.atomic_ally}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )
        self.log("Set normal command tree")

    def set_strat_saver_command_tree(self) -> None:
        
        # charge discharge relay reports to strat boss
        chg_dschg_node = self.layout.node(H0N.store_charge_discharge_relay)
        chg_dschg_node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{H0N.strat_boss}.{chg_dschg_node.Name}"

        # Thermostat relays report to strat boss
        for zone in self.layout.zone_list:
            failsafe_node = self.stat_failsafe_relay(zone)
            failsafe_node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{H0N.strat_boss}.{failsafe_node.Name}"
            stat_ops_node = self.stat_ops_relay(zone)
            stat_ops_node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{H0N.strat_boss}.{stat_ops_node.Name}"

        # dist pump and primary pump dfrs reports to strat boss
        dist_010_node = self.layout.node(H0N.dist_010v)
        primary_010_node = self.layout.node(H0N.primary_010v)
        dist_010_node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{H0N.strat_boss}.{dist_010_node.Name}"
        primary_010_node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{H0N.strat_boss}.{primary_010_node.Name}"

        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )
        self.log(f"Set strat saver command tree. E.g. charge/discharge is now {chg_dschg_node.handle}")
    
    def trigger_event(self, event: AtomicAllyEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        self.log(f"{event}: {orig_state} -> {self.state}")
        self._send_to(
            self.primary_scada,
            MachineStates(
                MachineHandle=self.node.handle,
                StateEnum=AtomicAllyState.enum_name(),
                StateList=[self.state],
                UnixMsList=[now_ms],
            ),
        )

        # Could update this to receive back reports from the relays and
        # add them to the report.
        trigger_id = str(uuid.uuid4())
        self._send_to(
            self.primary_scada,
            FsmFullReport(
                FromName=self.name,
                TriggerId=trigger_id,
                AtomicList=[
                    FsmAtomicReport(
                        MachineHandle=self.node.handle,
                        StateEnum=AtomicAllyState.enum_name(),
                        ReportType=FsmReportType.Event,
                        EventEnum=AtomicAllyEvent.enum_name(),
                        Event=event,
                        FromState=orig_state,
                        ToState=self.state,
                        UnixTimeMs=now_ms,
                        TriggerId=trigger_id,
                    )
                ],
            ),
        )

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.MAIN_LOOP_SLEEP_SECONDS * 2.1)]

    def suit_up(self) -> None:
        """Checks prerequisites and initializes AtomicAlly for dispatch contract participation.
    
        Sends GameOn to Atn if ready, logs failure if prerequisites not met.
        """
        if not self.forecasts:
            self.log("Cannot suit up - missing forecasts!")
            self._send_to(
                self.primary_scada,
                AllyGivesUp(
                        Reason="Missing forecasts required for operation"
                    )
                )
            return
            
        self.log("Suiting up")
        self._send_to(self.primary_scada, SuitUp(ToNode=H0N.primary_scada, FromNode=self.name))
        self.trigger_event(AtomicAllyEvent.WakeUp)
        self.engage_brain()

    def cancel_strat_boss(self):
        self._send_to(self.layout.node(H0N.strat_boss),
                      StratBossTrigger(
                          FromState=StratBossState.Active,
                          ToState=StratBossState.Dormant,
                          Trigger=StratBossEvent.BossCancels,
                      ),
                      self.layout.node(H0N.atomic_ally))

    def engage_brain(self) -> None:
        self.log(f"State: {self.state}")
        if self.state not in [AtomicAllyState.Dormant, AtomicAllyState.HpOffOilBoilerTankAquastat]:
            previous_state = self.state
            self.get_latest_temperatures()

            if (
                self.state == AtomicAllyState.WaitingNoElec
                or self.state == AtomicAllyState.WaitingElec
            ):
                if self.temperatures_available:
                    if self.no_more_elec():
                        if (
                            self.is_buffer_empty()
                            and not self.is_storage_colder_than_buffer()
                        ):
                            self.trigger_event(AtomicAllyEvent.NoElecBufferEmpty.value)
                        else:
                            self.trigger_event(AtomicAllyEvent.NoElecBufferFull.value)
                    else:
                        if self.is_buffer_empty() or self.is_storage_full():
                            self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                        else:
                            self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)
                elif (
                    self.state == AtomicAllyState.WaitingElec
                    and self.no_more_elec()
                ):
                    self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                elif (
                    self.state == AtomicAllyState.WaitingNoElec
                    and not self.no_more_elec()
                ):
                    self.trigger_event(AtomicAllyEvent.ElecAvailable.value)

            # 1
            elif self.state == AtomicAllyState.HpOnStoreOff.value:
                if self.no_more_elec() and datetime.now(self.timezone).minute<55:
                    self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                elif self.is_buffer_full() and not self.is_storage_full():
                    self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)
                elif self.is_buffer_full(really_full=True):
                    if not self.storage_declared_full or time.time()-self.storage_full_since>15*60:
                        self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)
                    if self.storage_declared_full and time.time()-self.storage_full_since<15*60:
                        self.log("Both storage and buffer are as full as can be")
                        self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                        # TODO: send message to ATN saying the EnergyInstruction will be violated

            # 2
            elif self.state == AtomicAllyState.HpOnStoreCharge.value:
                if self.no_more_elec() and datetime.now(self.timezone).minute<55:
                    self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                elif self.is_buffer_empty() or self.is_storage_full():
                    self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)

            # 3
            elif self.state == AtomicAllyState.HpOffStoreOff.value:
                if self.no_more_elec():
                    if (
                        self.is_buffer_empty()
                        and not self.is_storage_colder_than_buffer()
                    ):
                        self.trigger_event(AtomicAllyEvent.NoElecBufferEmpty.value)
                else:
                    if self.is_buffer_empty() or self.is_storage_full():
                        self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                    else:
                        self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)

            # 4
            elif self.state == AtomicAllyState.HpOffStoreDischarge.value:
                if self.no_more_elec():
                    if (
                        self.is_buffer_full()
                        or self.is_storage_colder_than_buffer()
                    ):
                        self.trigger_event(AtomicAllyEvent.NoElecBufferFull.value)
                else:
                    if self.is_buffer_empty() or self.is_storage_full():
                        self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                    else:
                        self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)

            if self.state != previous_state:
                self.update_relays(previous_state)

    async def main(self):
        await asyncio.sleep(2)
        while not self._stop_requested:
            self._send(PatInternalWatchdogMessage(src=self.name))
            self.engage_brain()
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def update_relays(self, previous_state: str) -> None:
        if self.state == AtomicAllyState.WaitingNoElec.value:
            self.turn_off_HP()
        if previous_state == AtomicAllyState.HpOffOilBoilerTankAquastat.value:
            self.hp_failsafe_switch_to_scada()
            self.aquastat_ctrl_switch_to_scada()
        if (self.state == AtomicAllyState.Dormant.value 
            or self.state==AtomicAllyState.WaitingElec.value
            or self.state==AtomicAllyState.WaitingNoElec.value):
            return
        if "HpOn" not in previous_state and "HpOn" in self.state:
            self.turn_on_HP()
        if "HpOff" not in previous_state and "HpOff" in self.state:
            self.turn_off_HP()
        if "StoreDischarge" in self.state:
            self.turn_on_store_pump()
        else:
            self.turn_off_store_pump()         
        if "StoreCharge" in self.state:
            self.valved_to_charge_store()
        else:
            self.valved_to_discharge_store()
        if self.state == AtomicAllyState.HpOffOilBoilerTankAquastat.value:
            self.hp_failsafe_switch_to_aquastat()
            self.aquastat_ctrl_switch_to_boiler()
        else:
            self.hp_failsafe_switch_to_scada()
            self.aquastat_ctrl_switch_to_scada()

    def fill_missing_store_temps(self):
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        for layer in all_store_layers:
            if (layer not in self.latest_temperatures 
            or self.latest_temperatures[layer] < 60
            or self.latest_temperatures[layer] > 200):
                self.latest_temperatures[layer] = None
        if H0CN.store_cold_pipe in self.latest_temperatures:
            value_below = self.latest_temperatures[H0CN.store_cold_pipe]
        else:
            value_below = 0
        for layer in sorted(all_store_layers, reverse=True):
            if self.latest_temperatures[layer] is None:
                self.latest_temperatures[layer] = value_below
            value_below = self.latest_temperatures[layer]  
        self.latest_temperatures = {k:self.latest_temperatures[k] for k in sorted(self.latest_temperatures)}

    def get_latest_temperatures(self):
        if not self.is_simulated:
            temp = {
                x: self.data.latest_channel_values[x] 
                for x in self.temperature_channel_names
                if x in self.data.latest_channel_values
                and self.data.latest_channel_values[x] is not None
                }
            self.latest_temperatures = temp.copy()
        else:
            self.log("IN SIMULATION - set all temperatures to 60 degC")
            self.latest_temperatures = {}
            for channel_name in self.temperature_channel_names:
                self.latest_temperatures[channel_name] = 60 * 1000
        for channel in self.latest_temperatures:
            if self.latest_temperatures[channel] is not None:
                self.latest_temperatures[channel] = self.to_fahrenheit(self.latest_temperatures[channel]/1000)
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
            print('Temperatures available')
        else:
            self.temperatures_available = False
            print('Some temperatures are missing')
            all_buffer = [x for x in self.temperature_channel_names if 'buffer-depth' in x]
            available_buffer = [x for x in list(self.latest_temperatures.keys()) if 'buffer-depth' in x]
            if all_buffer == available_buffer:
                print("All the buffer temperatures are available")
                self.fill_missing_store_temps()
                print("Successfully filled in the missing storage temperatures.")
                self.temperatures_available = True
        total_usable_kwh = self.data.latest_channel_values[H0N.usable_energy]
        required_storage = self.data.latest_channel_values[H0N.required_energy]
        if total_usable_kwh is None or required_storage is None:
            self.temperatures_available = False

    def initialize_actuators(self):
        my_relays =  {
            relay
            for relay in self.my_actuators()
            if relay.ActorClass == ActorClass.Relay and self.the_boss_of(relay) == self.node
        }

        target_relays: List[ShNode] = list(my_relays - {
                self.store_charge_discharge_relay, # keep as it was
                self.hp_failsafe_relay,
                self.hp_scada_ops_relay, # keep as it was unless on peak
                self.aquastat_control_relay
            }
        )
        target_relays.sort(key=lambda x: x.Name)
        self.log("de-energizing most relays")
        for relay in target_relays:
            self.de_energize(relay)

        self.log("Taking care of critical relays")
        self.hp_failsafe_switch_to_scada()
        self.aquastat_ctrl_switch_to_scada()
        if self.no_more_elec():
            self.turn_off_HP()

        try:
            self.set_010_defaults()
        except ValueError as e:
            self.log(f"Trouble with set_010_defaults: {e}")

    def set_010_defaults(self) -> None:
        dfr_component = cast(DfrComponent, self.layout.node(H0N.zero_ten_out_multiplexer).component)
        self.my_dfrs = [node for node in self.layout.nodes.values() if node.ActorClass == ActorClass.ZeroTenOutputer]
        for dfr_node in self.my_dfrs:
            dfr_config = next(
                    config
                    for config in dfr_component.gt.ConfigList
                    if config.ChannelName == dfr_node.name
                )
            self._send_to(
                dst=dfr_node,
                payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    FromHandle=self.node.handle,
                    ToHandle=dfr_node.handle,
                    AboutName=dfr_node.Name,
                    Value=dfr_config.InitialVoltsTimes100,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                )
            )
            self.log(f"Just set {dfr_node.handle} to {dfr_config.InitialVoltsTimes100} from {self.node.handle} ")            

    def no_more_elec(self) -> bool:
        if self.remaining_elec_wh is None or self.remaining_elec_wh <= 1:
            self.log("No electricity available")
            return True
        else:
            self.log(f"Electricity available: {self.remaining_elec_wh} Wh")
            return False
    
    def is_buffer_empty(self, really_empty=False) -> bool:
        if H0CN.buffer.depth2 in self.latest_temperatures:
            if really_empty:
                buffer_empty_ch = H0CN.buffer.depth1
            else:
                buffer_empty_ch = H0CN.buffer.depth2
        elif H0CN.dist_swt in self.latest_temperatures:
            buffer_empty_ch = H0CN.dist_swt
        else:
            self.alert(summary="buffer_empty_fail", details="Impossible to know if the buffer is empty!")
            return False
        max_rswt_next_3hours = max(self.forecasts.RswtF[:3])
        max_deltaT_rswt_next_3_hours = max(self.forecasts.RswtDeltaTF[:3])
        min_buffer = round(max_rswt_next_3hours - max_deltaT_rswt_next_3_hours,1)
        buffer_empty_ch_temp = round(self.latest_temperatures[buffer_empty_ch],1)
        if buffer_empty_ch_temp < min_buffer:
            self.log(f"Buffer empty ({buffer_empty_ch}: {buffer_empty_ch_temp} < {min_buffer} F)")
            return True
        else:
            self.log(f"Buffer not empty ({buffer_empty_ch}: {buffer_empty_ch_temp} >= {min_buffer} F)")
            return False            
    
    def is_buffer_full(self, really_full=False) -> bool:
        if H0CN.buffer.depth4 in self.latest_temperatures:
            buffer_full_ch = H0CN.buffer.depth4
        elif H0CN.buffer_cold_pipe in self.latest_temperatures:
            buffer_full_ch = H0CN.buffer_cold_pipe
        elif "StoreDischarge" in self.state and H0CN.store_cold_pipe in self.latest_temperatures:
            buffer_full_ch = H0CN.store_cold_pipe
        elif 'hp-ewt' in self.latest_temperatures:
            buffer_full_ch = 'hp-ewt'
        else:
            self.alert(summary="buffer_full_fail", details="Impossible to know if the buffer is full!")
            return False
        max_buffer = round(max(self.forecasts.RswtF[:3]),1)
        buffer_full_ch_temp = round(self.latest_temperatures[buffer_full_ch],1)

        if really_full:
            if H0CN.buffer_cold_pipe in self.latest_temperatures:
                buffer_full_ch_temp = round(self.latest_temperatures[H0CN.buffer_cold_pipe],1)
            max_buffer = self.params.MaxEwtF
            if buffer_full_ch_temp > max_buffer:
                self.log(f"Buffer cannot be charged more ({buffer_full_ch}: {buffer_full_ch_temp} > {max_buffer} F)")
                return True
            else:
                self.log(f"Buffer can be charged more ({buffer_full_ch}: {buffer_full_ch_temp} <= {max_buffer} F)")
                return False
            
        if buffer_full_ch_temp > max_buffer:
            self.log(f"Buffer full ({buffer_full_ch}: {buffer_full_ch_temp} > {max_buffer} F)")
            return True
        else:
            self.log(f"Buffer not full ({buffer_full_ch}: {buffer_full_ch_temp} <= {max_buffer} F)")
            return False
        
    def is_storage_full(self) -> bool:
        # Storage was declared full in the last 15 min
        if self.storage_declared_full and self.storage_full_since - time.time() < 15*60:
            return True
        if self.latest_temperatures[H0N.store_cold_pipe] > self.params.MaxEwtF: 
            self.log(f"Storage is full (store-cold-pipe > {self.params.MaxEwtF} F).")
            self.storage_declared_full = True
            self.storage_full_since = time.time()
            return True
        else:
            self.log(f"Storage is not full (store-cold-pipe <= {self.params.MaxEwtF} F).")
            self.storage_declared_full = False
            return False
        
    def is_storage_colder_than_buffer(self) -> bool:
        if H0CN.buffer.depth1 in self.latest_temperatures:
            buffer_top = H0CN.buffer.depth1
        elif H0CN.buffer.depth2 in self.latest_temperatures:
            buffer_top = H0CN.buffer.depth2
        elif H0CN.buffer.depth3 in self.latest_temperatures:
            buffer_top = H0CN.buffer.depth3
        elif H0CN.buffer.depth4 in self.latest_temperatures:
            buffer_top = H0CN.buffer.depth4
        elif H0CN.buffer_cold_pipe in self.latest_temperatures:
            buffer_top = H0CN.buffer_cold_pipe
        else:
            self.alert(summary="store_v_buffer_fail", details="It is impossible to know if the top of the buffer is warmer than the top of the storage!")
            return False
        if self.cn.tank[1].depth1 in self.latest_temperatures:
            tank_top = self.cn.tank[1].depth1
        elif H0CN.store_hot_pipe in self.latest_temperatures:
            tank_top = H0CN.store_hot_pipe
        elif H0CN.buffer_hot_pipe in self.latest_temperatures:
            tank_top = H0CN.buffer_hot_pipe
        else:
            self.alert(summary="store_v_buffer_fail", details="It is impossible to know if the top of the storage is warmer than the top of the buffer!")
            return False
        if self.latest_temperatures[buffer_top] > self.latest_temperatures[tank_top] + 3:
            self.log("Storage top colder than buffer top")
            return True
        else:
            print("Storage top warmer than buffer top")
            return False
        
    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32

    def alert(self, summary: str, details: str) -> None:
        msg =Glitch(
            FromGNodeAlias=self.layout.scada_g_node_alias,
            Node=self.node,
            Type=LogLevel.Critical,
            Summary=summary,
            Details=details
        )
        self._send_to(H0N.atn, msg)
        self.log(f"Glitch: {summary}")