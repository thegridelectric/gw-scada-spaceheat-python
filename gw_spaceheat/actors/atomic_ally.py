import asyncio
from typing import Optional, Sequence
from enum import auto
import uuid
import time
import json
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from pydantic import ValidationError
from gw.enums import GwStrEnum
from gwproactor import ServicesInterface,  MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from actors.scada_data import ScadaData
from result import Ok, Result
from transitions import Machine
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N, H0CN
from gwproto.enums import (ChangeRelayState, ChangeHeatPumpControl, ChangeAquastatControl, 
                           ChangeStoreFlowRelay, FsmReportType, MainAutoState)
from gwproto.named_types import (Alert, FsmEvent, Ha1Params, MachineStates, FsmAtomicReport,
                                 FsmFullReport, GoDormant, WakeUp, EnergyInstruction, PowerWatts)
from actors.config import ScadaSettings
from actors.scada_actor import ScadaActor
from actors.synth_generator import RemainingElec


class AtomicAllyState(GwStrEnum):
    WaitingElec = auto()
    WaitingNoElec = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()

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

    @classmethod
    def enum_name(cls) -> str:
        return "atomic.ally.event"


class AtomicAlly(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60

    states = [
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
    ]

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
        # Relays
        self.hardware_layout = self._services.hardware_layout
        self.hp_scada_ops_relay: ShNode = self.hardware_layout.node(H0N.hp_scada_ops_relay)
        self.hp_failsafe_relay: ShNode = self.hardware_layout.node(H0N.hp_failsafe_relay)
        self.aquastat_ctrl_relay: ShNode = self.hardware_layout.node(H0N.aquastat_ctrl_relay)
        self.store_pump_failsafe: ShNode = self.hardware_layout.node(H0N.store_pump_failsafe)
        self.store_charge_discharge_relay: ShNode = self.hardware_layout.node(H0N.store_charge_discharge_relay)
        # State machine
        self.machine = Machine(
            model=self,
            states=AtomicAlly.states,
            transitions=AtomicAlly.transitions,
            initial=AtomicAllyState.WaitingNoElec.value,
            send_event=True,
        )     
        self.state: AtomicAllyState = AtomicAllyState.WaitingNoElec  
        # House parameters in the .env file
        self.is_simulated = self.settings.is_simulated
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.latitude = self.settings.latitude
        self.longitude = self.settings.longitude
        # used by the rswt quad params calculator
        self._cached_params: Optional[Ha1Params] = None 
        self._rswt_quadratic_params: Optional[np.ndarray] = None 
        self.log(f"self.timezone: {self.timezone}")
        self.log(f"self.latitude: {self.latitude}")
        self.log(f"self.longitude: {self.longitude}")
        self.log(f"Params: {self.params}")
        self.log(f"self.is_simulated: {self.is_simulated}")
        # Weather forecast
        self.weather = None
        self.coldest_oat_by_month = [-3, -7, 1, 21, 30, 31, 46, 47, 28, 24, 16, 0]
        self.remaining_elec_wh = None
    
    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params

    @property
    def rswt_quadratic_params(self) -> np.ndarray:
        """Property to get quadratic parameters for calculating heating power 
        from required source water temp, recalculating if necessary
        """
        if self.params != self._cached_params:
            intermediate_rswt = self.params.IntermediateRswtF
            dd_rswt = self.params.DdRswtF
            intermediate_power = self.params.IntermediatePowerKw
            dd_power = self.params.DdPowerKw
            x_rswt = np.array([self.no_power_rswt, intermediate_rswt, dd_rswt])
            y_hpower = np.array([0, intermediate_power, dd_power])
            A = np.vstack([x_rswt**2, x_rswt, np.ones_like(x_rswt)]).T
            self._rswt_quadratic_params = np.linalg.solve(A, y_hpower)
            self._cached_params = self.params
            self.log(f"Calculating rswt_quadratic_params: {self._rswt_quadratic_params}")
        
        if self._rswt_quadratic_params is None:
            raise Exception("_rswt_quadratic_params should have been set here!!")
        return self._rswt_quadratic_params

    @property
    def no_power_rswt(self) -> float:
        alpha = self.params.AlphaTimes10 / 10
        beta = self.params.BetaTimes100 / 100
        return -alpha/beta

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
                # TODO: possibly add other state changes which need to happen asap
                if message.Payload.AvgPowerWatts == 0:
                    if "HpOn" in self.state:
                        self._turn_off_HP()
            case GoDormant():
                self._go_dormant_received(message.Payload)
            case RemainingElec():
                # TODO: perhaps 1 Wh is not the best number here
                if message.Payload.RemainingWattHours <= 1:
                    if "HpOn" in self.state:
                        self._turn_off_HP()
                self.remaining_elec_wh = message.Payload.RemainingWattHours
            case WakeUp():
                self._wake_up_received(message.Payload)
            
        return Ok(True)
    
    def _go_dormant_received(self) -> None:
        """
        Relays no longer belong to home alone until wake up received
        """
        ...
    
    def _wake_up_received(self) -> None:
        """
        Home alone is again in charge of things.
        """
        ...
    
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
        self._send_to(self.primary_scada,
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
                    ]
                ))
    
    async def main(self):

        await asyncio.sleep(2)
        
        while not self._stop_requested:
            
            # self._send(PatInternalWatchdogMessage(src=self.name))

            if self.services.auto_state != MainAutoState.Atn:
                self.log("State: DORMANT")
            else:
                self.log(f"State: {self.state}")
                previous_state = self.state

                if self.weather is None:
                    self.get_weather()
                else:
                    if datetime.now(self.timezone)>self.weather['time'][0]:
                        self.get_weather()

                self.get_latest_temperatures()

                if (self.state==AtomicAllyState.WaitingNoElec or self.state==AtomicAllyState.WaitingElec):
                    if self.temperatures_available:
                        if self.no_more_elec():
                            if self.is_buffer_empty() and not self.is_storage_colder_than_buffer():
                                self.trigger_event(AtomicAllyEvent.NoElecBufferEmpty.value)
                            else:
                                self.trigger_event(AtomicAllyEvent.NoElecBufferFull.value)
                        else:
                            if self.is_buffer_empty() or self.is_storage_full():
                                self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                            else:
                                self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)
                    elif self.state==AtomicAllyState.WaitingElec and self.no_more_elec():
                        self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                    elif self.state==AtomicAllyState.WaitingNoElec and not self.no_more_elec():
                        self.trigger_event(AtomicAllyEvent.ElecAvailable.value)

                # 1
                elif self.state==AtomicAllyState.HpOnStoreOff.value:
                    if self.no_more_elec():
                        self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                    elif self.is_buffer_full():
                        self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)
                    
                # 2
                elif self.state==AtomicAllyState.HpOnStoreCharge.value:
                    if self.no_more_elec():
                        self.trigger_event(AtomicAllyEvent.NoMoreElec.value)
                    elif self.is_buffer_empty() or self.is_storage_full():
                        self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                    
                # 3
                elif self.state==AtomicAllyState.HpOffStoreOff.value:
                    if self.no_more_elec():
                        if self.is_buffer_empty() and not self.is_storage_colder_than_buffer():
                            self.trigger_event(AtomicAllyEvent.NoElecBufferEmpty.value)
                    else:
                        if self.is_buffer_empty() or self.is_storage_full():
                            self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                        else:
                            self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)

                # 4
                elif self.state==AtomicAllyState.HpOffStoreDischarge.value:
                    if self.no_more_elec():
                        if self.is_buffer_full() or self.is_storage_colder_than_buffer():
                            self.trigger_event(AtomicAllyEvent.NoElecBufferFull.value)
                    else:
                        if self.is_buffer_empty() or self.is_storage_full():
                            self.trigger_event(AtomicAllyEvent.ElecBufferEmpty.value)
                        else:
                            self.trigger_event(AtomicAllyEvent.ElecBufferFull.value)

                if self.state != previous_state:                    
                    self.update_relays(previous_state)

            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def update_relays(self, previous_state) -> None:
        if self.state==AtomicAllyState.WaitingNoElec.value:
            self._turn_off_HP()
        if "HpOn" not in previous_state and "HpOn" in self.state:
            self._turn_on_HP()
        if "HpOff" not in previous_state and "HpOff" in self.state:
            self._turn_off_HP()
        if "StoreDischarge" in self.state:
            self._turn_on_store()
        if "StoreDischarge" not in self.state:
            self._turn_off_store()
        if "StoreCharge" not in previous_state and "StoreCharge" in self.state:
            self._valved_to_charge_store()
        if "StoreCharge" in previous_state and "StoreCharge" not in self.state:
            self._valved_to_discharge_store()

    def _turn_on_HP(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.hp_scada_ops_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            self._send_to(self.hp_scada_ops_relay, event)
            self.log(f"{self.node.handle} sending CloseRelay to Hp ScadaOps {H0N.hp_scada_ops_relay}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def _turn_off_HP(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.hp_scada_ops_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            
            self._send_to(self.hp_scada_ops_relay, event)
            self.log(f"{self.node.handle} sending OpenRelay to Hp ScadaP[s {H0N.hp_scada_ops_relay}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def _turn_on_store(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.store_pump_failsafe.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            self._send_to(self.store_pump_failsafe, event)
            self.log(f"{self.node.handle} sending CloseRelay to StorePump OnOff {H0N.store_pump_failsafe}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def _turn_off_store(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.store_pump_failsafe.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            self._send_to(self.store_pump_failsafe, event)
            self.log(f"{self.node.handle} sending OpenRelay to StorePump OnOff {H0N.store_pump_failsafe}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def _valved_to_charge_store(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.store_charge_discharge_relay.handle,
                EventType=ChangeStoreFlowRelay.enum_name(),
                EventName=ChangeStoreFlowRelay.ChargeStore,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            self._send_to(self.store_charge_discharge_relay, event)
            self.log(f"{self.node.handle} sending ChargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def _valved_to_discharge_store(self) -> None:
        try:
            event = FsmEvent(
                FromHandle='auto.h',
                ToHandle=self.store_charge_discharge_relay.handle,
                EventType=ChangeStoreFlowRelay.enum_name(),
                EventName=ChangeStoreFlowRelay.DischargeStore,
                SendTimeUnixMs=int(time.time()*1000),
                TriggerId=str(uuid.uuid4()),
                )
            self._send_to(self.store_charge_discharge_relay, event)
            self.log(f"{self.node.handle} sending DischargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

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
        if self.no_more_elec():
            self._turn_off_HP()
        event = FsmEvent(
            FromHandle='auto.h',
            ToHandle=self.hp_failsafe_relay.handle,
            EventType=ChangeHeatPumpControl.enum_name(),
            EventName=ChangeHeatPumpControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_failsafe_relay, event)
        self.log(f"{self.node.handle} sending SwitchToScada to Hp Failsafe {H0N.hp_failsafe_relay}")
        event = FsmEvent(
            FromHandle='auto.h',
            ToHandle=self.aquastat_ctrl_relay.handle,
            EventType=ChangeAquastatControl.enum_name(),
            EventName=ChangeAquastatControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.aquastat_ctrl_relay, event)
        self.log(f"{self.node.handle} sending SwitchToScada to Aquastat Ctrl {H0N.aquastat_ctrl_relay}")

    def no_more_elec(self) -> bool:
        if self.remaining_elec_wh is None:
            return True
        if self.remaining_elec_wh <= 1:
            self.log("No electricity available")
            return True
        else:
            self.log(f"Electricity available: {self.remaining_elec_wh} Wh")
            return False
    
    def is_buffer_empty(self) -> bool:
        if H0CN.buffer.depth2 in self.latest_temperatures:
            buffer_empty_ch = H0CN.buffer.depth2
        elif H0CN.dist_swt in self.latest_temperatures:
            buffer_empty_ch = H0CN.dist_swt
        else:
            self.alert(alias="buffer_empty_fail", msg="Impossible to know if the buffer is empty!")
            return False
        max_rswt_next_3hours = max(self.weather['required_swt'][:3])
        min_buffer = round(max_rswt_next_3hours - self.delta_T(max_rswt_next_3hours),1)
        if self.latest_temperatures[buffer_empty_ch] < min_buffer:
            self.log(f"Buffer empty ({buffer_empty_ch}: {round(self.latest_temperatures[buffer_empty_ch],1)} < {min_buffer} F)")
            return True
        else:
            self.log(f"Buffer not empty ({buffer_empty_ch}: {round(self.latest_temperatures[buffer_empty_ch],1)} >= {min_buffer} F)")
            return False            
    
    def is_buffer_full(self) -> bool:
        if H0CN.buffer.depth4 in self.latest_temperatures:
            buffer_full_temp = H0CN.buffer.depth4
        elif H0CN.buffer_cold_pipe in self.latest_temperatures:
            buffer_full_temp = H0CN.buffer_cold_pipe
        elif "StoreDischarge" in self.state and H0CN.store_cold_pipe in self.latest_temperatures:
            buffer_full_temp = H0CN.store_cold_pipe
        elif 'hp-ewt' in self.latest_temperatures:
            buffer_full_temp = 'hp-ewt'
        else:
            self.alert(alias="buffer_full_fail", msg="Impossible to know if the buffer is full!")
            return False
        max_buffer = round(max(self.weather['required_swt'][:3]),1)
        if self.latest_temperatures[buffer_full_temp] > max_buffer:
            self.log(f"Buffer full (layer 4: {round(self.latest_temperatures[buffer_full_temp],1)} > {max_buffer} F)")
            return True
        else:
            self.log(f"Buffer not full (layer 4: {round(self.latest_temperatures[buffer_full_temp],1)} <= {max_buffer} F)")
            return False
        
    def is_storage_full(self) -> bool:
        if self.latest_temperatures[H0N.store_cold_pipe] > self.params.MaxEwtF:
            self.log(f"Storage is full (store-cold-pipe > {self.params.MaxEwtF} F).")
            return True
        else:
            self.log(f"Storage is not full (store-cold-pipe <= {self.params.MaxEwtF} F).")
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
        if self.latest_temperatures[buffer_top] > self.latest_temperatures[tank_top]:
            self.log("Storage top colder than buffer top")
            return True
        else:
            print("Storage top warmer than buffer top")
            return False
        
    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32
    
    def required_heating_power(self, oat: float, wind_speed_mph: float) -> float:
        ws = wind_speed_mph
        alpha = self.params.AlphaTimes10 / 10
        beta = self.params.BetaTimes100 / 100
        gamma = self.params.GammaEx6 / 1e6
        r = alpha + beta*oat + gamma*ws
        return round(r,2) if r>0 else 0

    def required_swt(self, required_kw_thermal: float) -> float:
        rhp = required_kw_thermal
        a, b, c = self.rswt_quadratic_params
        return round(-b/(2*a) + ((rhp-b**2/(4*a)+b**2/(2*a)-c)/a)**0.5,2)
        
    def get_weather(self) -> None:
        config_dir = self.settings.paths.config_dir
        weather_file = config_dir / "weather.json"
        try:
            url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
            response = requests.get(url)
            if response.status_code != 200:
                self.log(f"Error fetching weather data: {response.status_code}")
                return None
            data = response.json()
            forecast_hourly_url = data['properties']['forecastHourly']
            forecast_response = requests.get(forecast_hourly_url)
            if forecast_response.status_code != 200:
                self.log(f"Error fetching hourly weather forecast: {forecast_response.status_code}")
                return None
            forecast_data = forecast_response.json()
            forecasts = {}
            periods = forecast_data['properties']['periods']
            for period in periods:
                if ('temperature' in period and 'startTime' in period 
                    and datetime.fromisoformat(period['startTime'])>datetime.now(tz=self.timezone)):
                    forecasts[datetime.fromisoformat(period['startTime'])] = period['temperature']
            forecasts = dict(list(forecasts.items())[:96])
            cropped_forecast = dict(list(forecasts.items())[:24])
            self.weather = {
                'time': list(cropped_forecast.keys()),
                'oat': list(cropped_forecast.values()),
                'ws': [0]*len(cropped_forecast)
                }
            self.log(f"Obtained a {len(forecasts)}-hour weather forecast starting at {self.weather['time'][0]}")
            weather_long = {
                'time': [x.timestamp() for x in list(forecasts.keys())],
                'oat': list(forecasts.values()),
                'ws': [0]*len(forecasts)
                }
            with open(weather_file, 'w') as f:
                json.dump(weather_long, f, indent=4)
        
        except Exception as e:
            self.log(f"[!] Unable to get weather forecast from API: {e}")
            try:
                with open(weather_file, 'r') as f:
                    weather_long = json.load(f)
                    weather_long['time'] = [datetime.fromtimestamp(x, tz=self.timezone) for x in weather_long['time']]
                if weather_long['time'][-1] >= datetime.fromtimestamp(time.time(), tz=self.timezone)+timedelta(hours=24):
                    self.log("A valid weather forecast is available locally.")
                    time_late = weather_long['time'][0] - datetime.now(self.timezone)
                    hours_late = int(time_late.total_seconds()/3600)
                    self.weather = weather_long
                    for key in self.weather:
                        self.weather[key] = self.weather[key][hours_late:hours_late+24]
                else:
                    self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                    current_month = datetime.now().month-1
                    self.weather = {
                        'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                        'oat': [self.coldest_oat_by_month[current_month]]*24,
                        'ws': [0]*24,
                        }
            except Exception as e:
                self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                current_month = datetime.now().month-1
                self.weather = {
                    'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                    'oat': [self.coldest_oat_by_month[current_month]]*24,
                    'ws': [0]*24,
                    }

        self.weather['avg_power'] = [
            self.required_heating_power(oat, ws) 
            for oat, ws in zip(self.weather['oat'], self.weather['ws'])
            ]
        self.weather['required_swt'] = [
            self.required_swt(x) 
            for x in self.weather['avg_power']
            ]
        self.log(f"OAT = {self.weather['oat']}")
        self.log(f"Average Power = {self.weather['avg_power']}")
        self.log(f"RSWT = {self.weather['required_swt']}")
        self.log(f"DeltaT at RSWT = {[round(self.delta_T(x),2) for x in self.weather['required_swt']]}")

    def delta_T(self, swt: float) -> float:
        a, b, c = self.rswt_quadratic_params
        delivered_heat_power = a*swt**2 + b*swt + c
        dd_delta_t = self.params.DdDeltaTF
        dd_power = self.params.DdPowerKw
        d = dd_delta_t/dd_power * delivered_heat_power
        return d if d>0 else 0
    
    def rwt(self, swt: float, return_rswt_onpeak=False) -> float:
        timenow = datetime.now(self.timezone)
        if timenow.hour > 19 or timenow.hour < 7:
            required_swt = max(
                [rswt for t, rswt in zip(self.weather['time'], self.weather['required_swt'])
                if t.hour in [7,8,9,10,11,16,17,18,19]]
                )
        else:
            required_swt = max(
                [rswt for t, rswt in zip(self.weather['time'], self.weather['required_swt'])
                if t.hour in [16,17,18,19]]
                )
        if return_rswt_onpeak:
            return required_swt
        if swt < required_swt - 10:
            delta_t = 0
        elif swt < required_swt:
            delta_t = self.delta_T(required_swt) * (swt-(required_swt-10))/10
        else:
            delta_t = self.delta_T(swt)
        return round(swt - delta_t,2)

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