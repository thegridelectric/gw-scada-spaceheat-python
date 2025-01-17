import asyncio
import time
import uuid
from enum import auto
from typing import Sequence
from datetime import datetime

import pytz
from data_classes.house_0_names import H0CN, H0N
from gw.enums import GwStrEnum
from gwproactor import MonitoredName, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.enums import FsmReportType
from gwproto.named_types import (Alert, FsmAtomicReport, FsmFullReport,
                                 MachineStates)
from named_types import EnergyInstruction, GoDormant, Ha1Params, WakeUp, HeatingForecast
from result import Ok, Result
from transitions import Machine

from actors.scada_actor import ScadaActor
from actors.scada_data import ScadaData
from named_types import RemainingElec, GameOn


class AtomicAllyState(GwStrEnum): 
    WaitingElec = auto()
    WaitingNoElec = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()
    Dormant = auto()


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
    ]

    transitions = [
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
    ]+ [
            {"trigger": "GoDormant", "source": state, "dest": "Dormant"}
            for state in states if state != "Dormant"
    ] + [{"trigger":"WakeUp", "source": "Dormant", "dest": "WaitingNoElec"}]

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
        match message.Payload:
            case EnergyInstruction():
                self.log(f"Received an EnergyInstruction for {message.Payload.AvgPowerWatts} Watts average power")
                self.remaining_elec_wh = message.Payload.AvgPowerWatts
                self.check_and_update_state()
            case GoDormant():
                if self.state != AtomicAllyState.Dormant.value:
                    # GoDormant: AnyOther -> Dormant ...
                    self.trigger_event(AtomicAllyEvent.GoDormant)
                    self.log("Going dormant")
            case RemainingElec():
                # TODO: perhaps 1 Wh is not the best number here
                if message.Payload.RemainingWattHours <= 1:
                    if "HpOn" in self.state:
                        self.turn_off_HP()
                self.remaining_elec_wh = message.Payload.RemainingWattHours
            case WakeUp():
                if self.state == AtomicAllyState.Dormant.value:
                    # WakeUp: Dormant -> WaitingNoElec ... will turn off heat pmp
                    # TODO: think through whether atomic ally also needs an init
                    # state. Note it will always be coming from HomeAlone
                    # WakeUp: Dormant -> WaitingNoElec ... will turn off heat pmp
                    self.trigger_event(AtomicAllyEvent.WakeUp)
                    self.check_and_update_state()
            case HeatingForecast():
                self.log("Received forecast")
                self.forecasts: HeatingForecast = message.Payload

        return Ok(True)
    
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

    def check_and_update_state(self) -> None:
        self.log(f"State: {self.state}")
        if not self.forecasts:
            self.log("Strange ... Do not have forecasts yet! Not updating state since can't check buffer state")
            return
        if self.state != AtomicAllyState.Dormant:
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
                    self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)

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
        self._send_to(self.primary_scada, GameOn(FromGNodeAlias=self.layout.atn_g_node_alias))
        # SynthGenerator gets forecasts ASAP on boot, including various fallbacks
        # if the request does not work. So wait a bit if 
        if self.forecasts is None:
            await asyncio.sleep(5)
        if self.forecasts is None:
            raise Exception("No access to forecasts! Won't be able to heat the buffer")
            
        while not self._stop_requested:
            self._send(PatInternalWatchdogMessage(src=self.name))
            self.check_and_update_state()
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def update_relays(self, previous_state: str) -> None:
        if self.state == AtomicAllyState.WaitingNoElec.value:
            self.turn_off_HP()
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

    def initialize_relays(self):
        self.hp_failsafe_switch_to_scada()
        self.aquastat_ctrl_switch_to_scada()
        if self.no_more_elec():
            self.turn_off_HP()

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
            self.alert(alias="buffer_empty_fail", msg="Impossible to know if the buffer is empty!")
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
            self.alert(alias="buffer_full_fail", msg="Impossible to know if the buffer is full!")
            return False
        max_buffer = round(max(self.forecasts.RswtF[:3]),1)
        buffer_full_ch_temp = round(self.latest_temperatures[buffer_full_ch],1)

        if really_full:
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
            self.alert(alias="store_v_buffer_fail", msg="It is impossible to know if the top of the buffer is warmer than the top of the storage!")
            return False
        if self.cn.tank[1].depth1 in self.latest_temperatures:
            tank_top = self.cn.tank[1].depth1
        elif H0CN.store_hot_pipe in self.latest_temperatures:
            tank_top = H0CN.store_hot_pipe
        elif H0CN.buffer_hot_pipe in self.latest_temperatures:
            tank_top = H0CN.buffer_hot_pipe
        else:
            self.alert(alias="store_v_buffer_fail", msg="It is impossible to know if the top of the storage is warmer than the top of the buffer!")
            return False
        if self.latest_temperatures[buffer_top] > self.latest_temperatures[tank_top] + 3:
            self.log("Storage top colder than buffer top")
            return True
        else:
            print("Storage top warmer than buffer top")
            return False
        
    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32

    def alert(self, alias: str, msg: str) -> None:
        alert_str = f"[ALERT] {msg}"
        self._services._links.publish_upstream(payload=Alert(
            FromGNodeAlias=self.layout.scada_g_node_alias,
            AboutNode=self.node,
            OpsGenieAlias=alias,
            UnixS=int(time.time()),
            Summary=msg
        ))
        self.log(alert_str)