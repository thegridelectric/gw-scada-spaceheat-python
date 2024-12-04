import asyncio
from typing import Any, Optional, Sequence
from enum import auto
import uuid
import time
import json
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from gw.enums import GwStrEnum
from gwproactor import Actor, ServicesInterface,  MonitoredName
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
                                 FsmFullReport, GoDormant, WakeUp)
from actors.config import ScadaSettings


class HomeAloneState(GwStrEnum):
    WaitingForTemperaturesOnPeak = auto()
    WaitingForTemperaturesOffPeak = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "home.alone.state"


class HomeAloneEvent(GwStrEnum):
    OnPeakStart = auto()
    OffPeakStart = auto()
    OnPeakBufferFull = auto()
    OffPeakBufferFullStorageNotReady = auto()
    OffPeakBufferFullStorageReady = auto()
    OffPeakBufferEmpty = auto()
    OnPeakBufferEmpty = auto()
    OffPeakStorageReady = auto()
    OffPeakStorageNotReady = auto()
    TemperaturesAvailable = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "home.alone.event"


class HomeAlone(Actor):
    MAIN_LOOP_SLEEP_SECONDS = 60
    states = [
        "WaitingForTemperaturesOnPeak",
        "WaitingForTemperaturesOffPeak",
        "HpOnStoreOff",
        "HpOnStoreCharge",
        "HpOffStoreOff",
        "HpOffStoreDischarge",
    ]

    transitions = [
        # Waiting for temperatures onpeak
        {"trigger": "OffPeakStart", "source": "WaitingForTemperaturesOnPeak", "dest": "WaitingForTemperaturesOffPeak"},
        {"trigger": "OnPeakBufferEmpty", "source": "WaitingForTemperaturesOnPeak", "dest": "HpOffStoreDischarge"},
        {"trigger": "OnPeakBufferFull", "source": "WaitingForTemperaturesOnPeak", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferEmpty", "source": "WaitingForTemperaturesOnPeak", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakBufferFullStorageReady", "source": "WaitingForTemperaturesOnPeak", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferFullStorageNotReady", "source": "WaitingForTemperaturesOnPeak", "dest": "HpOnStoreCharge"},
        # Waiting for temperatures offpeak
        {"trigger": "OnPeakStart", "source": "WaitingForTemperaturesOffPeak", "dest": "WaitingForTemperaturesOnPeak"},
        {"trigger": "OnPeakBufferEmpty", "source": "WaitingForTemperaturesOffPeak", "dest": "HpOffStoreDischarge"},
        {"trigger": "OnPeakBufferFull", "source": "WaitingForTemperaturesOffPeak", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferEmpty", "source": "WaitingForTemperaturesOffPeak", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakBufferFullStorageReady", "source": "WaitingForTemperaturesOffPeak", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferFullStorageNotReady", "source": "WaitingForTemperaturesOffPeak", "dest": "HpOnStoreCharge"},
        # Starting at: HP on, Store off ============= HP -> buffer
        {"trigger": "OffPeakBufferFullStorageNotReady", "source": "HpOnStoreOff", "dest": "HpOnStoreCharge"},
        {"trigger": "OffPeakBufferFullStorageReady", "source": "HpOnStoreOff", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStart", "source": "HpOnStoreOff", "dest": "HpOffStoreOff"},
        # Starting at: HP on, Store charging ======== HP -> storage
        {"trigger": "OffPeakBufferEmpty", "source": "HpOnStoreCharge", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakStorageReady", "source": "HpOnStoreCharge", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStart", "source": "HpOnStoreCharge", "dest": "HpOffStoreOff"},
        # Starting at: HP off, Store off ============ idle
        {"trigger": "OnPeakBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOffStoreDischarge"},
        {"trigger": "OffPeakBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakStorageNotReady", "source": "HpOffStoreOff", "dest": "HpOnStoreCharge"},
        # Starting at: Hp off, Store discharging ==== Storage -> buffer
        {"trigger": "OnPeakBufferFull", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakStart", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
    ]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.settings: ScadaSettings = self.services.settings
        self.cn: H0CN = self.layout.channel_names
        
        self._stop_requested: bool = False
        self.hardware_layout = self._services.hardware_layout
        self.temperature_channel_names = [
            H0CN.buffer.depth1, H0CN.buffer.depth2, H0CN.buffer.depth3, H0CN.buffer.depth4,
            H0CN.hp_ewt, H0CN.hp_lwt, H0CN.dist_swt, H0CN.dist_rwt, 
            H0CN.buffer_cold_pipe, H0CN.buffer_hot_pipe, H0CN.store_cold_pipe, H0CN.store_hot_pipe,
            *(depth for tank in self.cn.tank.values() for depth in [tank.depth1, tank.depth2, tank.depth3, tank.depth4])
        ]

        self.temperatures_available = False
        self.storage_declared_ready = False
        self.full_storage_energy = None
        # Relays
        self.hp_scada_ops_relay: ShNode = self.hardware_layout.node(H0N.hp_scada_ops_relay)
        self.hp_failsafe_relay: ShNode = self.hardware_layout.node(H0N.hp_failsafe_relay)
        self.aquastat_ctrl_relay: ShNode = self.hardware_layout.node(H0N.aquastat_ctrl_relay)
        self.store_pump_failsafe: ShNode = self.hardware_layout.node(H0N.store_pump_failsafe)
        self.store_charge_discharge_relay: ShNode = self.hardware_layout.node(H0N.store_charge_discharge_relay)
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=HomeAloneState.WaitingForTemperaturesOnPeak.value,
            send_event=True,
        )     
        self.state: HomeAloneState = HomeAloneState.WaitingForTemperaturesOnPeak  
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
        
        # Get the weather forecast
        self.weather = None
        self.coldest_oat_by_month = [-3, -7, 1, 21, 30, 31, 46, 47, 28, 24, 16, 0]
        self.get_weather()
    
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

    def trigger_event(self, event: HomeAloneEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        self.log(f"{event}: {orig_state} -> {self.state}")
        self._send_to(
            self.primary_scada,
            MachineStates(
                MachineHandle=self.node.handle,
                StateEnum=HomeAloneState.enum_name(),
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
                            StateEnum=HomeAloneState.enum_name(),
                            ReportType=FsmReportType.Event,
                            EventEnum=HomeAloneEvent.enum_name(),
                            Event=event,
                            FromState=orig_state,
                            ToState=self.state,
                            UnixTimeMs=now_ms,
                            TriggerId=trigger_id,
                        )
                    ]
                ))

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.MAIN_LOOP_SLEEP_SECONDS * 2.1)]

    async def main(self):

        await asyncio.sleep(2)
        self.initialize_relays()

        while not self._stop_requested:
            #self.log("PATTING HOME ALONE WATCHDOG")
            self._send(PatInternalWatchdogMessage(src=self.name))

            if self.services.auto_state != MainAutoState.HomeAlone:
                self.log("State: DORMANT")
            else:
                self.log(f"State: {self.state}")
                previous_state = self.state

                if self.is_onpeak():
                    self.storage_declared_ready = False
                    self.full_storage_energy = None

                if datetime.now(self.timezone)>self.weather['time'][0]:
                    self.get_weather()

                self.get_latest_temperatures()

                if (self.state==HomeAloneState.WaitingForTemperaturesOnPeak 
                    or self.state==HomeAloneState.WaitingForTemperaturesOffPeak):
                    if self.temperatures_available:
                        if self.is_onpeak():
                            if self.is_buffer_empty():
                                if self.is_storage_colder_than_buffer():
                                    self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)
                                else:
                                    self.trigger_event(HomeAloneEvent.OnPeakBufferEmpty.value)
                            else:
                                self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)
                        else:
                            if self.is_buffer_empty():
                                self.trigger_event(HomeAloneEvent.OffPeakBufferEmpty.value)
                            else:
                                if self.is_storage_ready():
                                    self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageReady)
                                else:
                                    self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady)
                    elif self.state==HomeAloneState.WaitingForTemperaturesOffPeak:
                        if self.is_onpeak():
                            self.trigger_event(HomeAloneEvent.OnPeakStart.value)
                    else:
                        if not self.is_onpeak():
                            self.trigger_event(HomeAloneEvent.OffPeakStart.value)

                elif self.state==HomeAloneState.HpOnStoreOff.value:
                    if self.is_onpeak():
                        self.trigger_event(HomeAloneEvent.OnPeakStart.value)
                    elif self.is_buffer_full():
                        if self.is_storage_ready():
                            self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageReady.value)
                        elif self.full_storage_energy is None:
                            self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady.value)
                        else:
                            self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageReady.value)
                    
                elif self.state==HomeAloneState.HpOnStoreCharge.value:
                    if self.is_onpeak():
                        self.trigger_event(HomeAloneEvent.OnPeakStart.value)
                    elif self.is_buffer_empty():
                        self.trigger_event(HomeAloneEvent.OffPeakBufferEmpty.value)
                    elif self.is_storage_ready():
                        self.trigger_event(HomeAloneEvent.OffPeakStorageReady.value)
                    
                elif self.state==HomeAloneState.HpOffStoreOff.value:
                    if self.is_onpeak():
                        if self.is_buffer_empty():
                            if not self.is_storage_colder_than_buffer():
                                self.trigger_event(HomeAloneEvent.OnPeakBufferEmpty.value)
                    else:
                        if self.is_buffer_empty():
                            self.trigger_event(HomeAloneEvent.OffPeakBufferEmpty.value)
                        elif not self.is_storage_ready():
                            usable, required = self.is_storage_ready(return_missing=True)
                            if self.storage_declared_ready:
                                if self.full_storage_energy is None:
                                    if usable > 0.9*required:
                                        self.log("The storage was already declared ready during this off-peak period")
                                    else:
                                        self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)
                                else:
                                    if usable > 0.9*self.full_storage_energy:
                                        self.log("The storage was already declared full during this off-peak period")
                                    else:
                                        self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)
                            else:
                                self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)

                elif self.state==HomeAloneState.HpOffStoreDischarge.value:
                    if not self.is_onpeak():
                        self.trigger_event(HomeAloneEvent.OffPeakStart.value)
                    elif self.is_buffer_full() or self.is_storage_colder_than_buffer():
                        self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)

                if self.state != previous_state:                    
                    self.update_relays(previous_state)

            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def update_relays(self, previous_state) -> None:
        if self.state==HomeAloneState.WaitingForTemperaturesOnPeak.value:
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
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_scada_ops_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_scada_ops_relay, event)
        self.log(f"{self.node.handle} sending CloseRelay to Hp ScadaOps {H0N.hp_scada_ops_relay}")

    def _turn_off_HP(self) -> None:
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_scada_ops_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        
        self._send_to(self.hp_scada_ops_relay, event)
        self.log(f"{self.node.handle} sending OpenRelay to Hp ScadaP[s {H0N.hp_scada_ops_relay}")

    def _turn_on_store(self) -> None:
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_failsafe.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_failsafe, event)
        self.log(f"{self.node.handle} sending CloseRelay to StorePump OnOff {H0N.store_pump_failsafe}")


    def _turn_off_store(self) -> None:
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_failsafe.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_failsafe, event)
        self.log(f"{self.node.handle} sending OpenRelay to StorePump OnOff {H0N.store_pump_failsafe}")


    def _valved_to_charge_store(self) -> None:
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_charge_discharge_relay.handle,
            EventType=ChangeStoreFlowRelay.enum_name(),
            EventName=ChangeStoreFlowRelay.ChargeStore,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_charge_discharge_relay, event)
        self.log(f"{self.node.handle} sending ChargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")

    def _valved_to_discharge_store(self) -> None:
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_charge_discharge_relay.handle,
            EventType=ChangeStoreFlowRelay.enum_name(),
            EventName=ChangeStoreFlowRelay.DischargeStore,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_charge_discharge_relay, event)
        self.log(f"{self.node.handle} sending DischargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="HomeAlone keepalive")
        )

    def stop(self) -> None:
        self._stop_requested = True
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case GoDormant():
                self._go_dormant_received(message.Payload)
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

    def change_all_temps(self, temp_c) -> None:
        if self.is_simulated:
            for channel_name in self.temperature_channel_names:
                self.change_temp(channel_name, temp_c)
        else:
            print("This function is only available in simulation")

    def change_temp(self, channel_name, temp_c) -> None:
        if self.is_simulated:
            self.latest_temperatures[channel_name] = temp_c * 1000
        else:
            print("This function is only available in simulation")

    def fill_missing_store_temps(self):
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        for layer in all_store_layers:
            if (layer not in self.latest_temperatures 
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) < 70
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) > 200):
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
        temp = {
            x: self.data.latest_channel_values[x] 
            for x in self.temperature_channel_names
            if x in self.data.latest_channel_values
            and self.data.latest_channel_values[x] is not None
            }
        self.latest_temperatures = temp.copy()
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
    
    def initialize_relays(self):
        if self.is_onpeak:
            self._turn_off_HP()
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_failsafe_relay.handle,
            EventType=ChangeHeatPumpControl.enum_name(),
            EventName=ChangeHeatPumpControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_failsafe_relay, event)
        self.log(f"{self.node.handle} sending SwitchToScada to Hp Failsafe {H0N.hp_failsafe_relay}")
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.aquastat_ctrl_relay.handle,
            EventType=ChangeAquastatControl.enum_name(),
            EventName=ChangeAquastatControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.aquastat_ctrl_relay, event)
        self.log(f"{self.node.handle} sending SwitchToScada to Aquastat Ctrl {H0N.aquastat_ctrl_relay}")

    def is_onpeak(self) -> bool:
        time_now = datetime.now(self.timezone)
        time_in_2min = time_now + timedelta(minutes=2)
        peak_hours = [7,8,9,10,11] + [16,17,18,19]
        if (time_now.hour in peak_hours or time_in_2min.hour in peak_hours):
            # and time_now.weekday() < 5):
            self.log("On-peak")
            return True
        else:
            self.log("Not on-peak")
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
        if self.latest_temperatures[buffer_empty_ch]/1000*9/5+32 < min_buffer: # TODO use to_fahrenheit()
            self.log(f"Buffer empty ({buffer_empty_ch}: {round(self.latest_temperatures[buffer_empty_ch]/1000*9/5+32,1)} < {min_buffer} F)")
            return True
        else:
            self.log(f"Buffer not empty ({buffer_empty_ch}: {round(self.latest_temperatures[buffer_empty_ch]/1000*9/5+32,1)} >= {min_buffer} F)")
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
        if self.latest_temperatures[buffer_full_temp]/1000*9/5+32 > max_buffer: # TODO use to_fahrenheit()
            self.log(f"Buffer full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)} > {max_buffer} F)")
            return True
        else:
            self.log(f"Buffer not full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)} <= {max_buffer} F)")
            return False

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
       
    def get_required_storage(self, time_now: datetime) -> float:
        morning_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 7<=t.hour<=11]
            )
        midday_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 12<=t.hour<=15]
            )
        afternoon_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 16<=t.hour<=19]
            )
        # if (((time_now.weekday()<4 or time_now.weekday()==6) and time_now.hour>=20)
        #     or (time_now.weekday()<5 and time_now.hour<=6)):
        if (time_now.hour>=20 or time_now.hour<=6):
            self.log('Preparing for a morning onpeak + afternoon onpeak')
            afternoon_missing_kWh = afternoon_kWh - (4*self.params.HpMaxKwTh - midday_kWh) # TODO make the kW_th a function of COP and kW_el
            return morning_kWh if afternoon_missing_kWh<0 else morning_kWh + afternoon_missing_kWh
        # elif (time_now.weekday()<5 and time_now.hour>=12 and time_now.hour<16):
        elif (time_now.hour>=12 and time_now.hour<16):
            self.log('Preparing for an afternoon onpeak')
            return afternoon_kWh
        else:
            self.log('No onpeak period coming up soon')
            return 0

    def is_storage_ready(self, return_missing=False) -> bool:
        time_now = datetime.now(self.timezone)
        latest_temperatures = self.latest_temperatures.copy()
        storage_temperatures = {k:v for k,v in latest_temperatures.items() if 'tank' in k}
        simulated_layers = [self.to_fahrenheit(v/1000) for k,v in storage_temperatures.items()]        
        total_usable_kwh = 0
        while True:
            if round(self.rwt(simulated_layers[0])) == round(simulated_layers[0]):
                simulated_layers = [sum(simulated_layers)/len(simulated_layers) for x in simulated_layers]
                if round(self.rwt(simulated_layers[0])) == round(simulated_layers[0]):
                    break
            total_usable_kwh += 360/12*3.78541 * 4.187/3600 * (simulated_layers[0]-self.rwt(simulated_layers[0]))*5/9
            simulated_layers = simulated_layers[1:] + [self.rwt(simulated_layers[0])]          
        required_storage = self.get_required_storage(time_now)
        if return_missing:
            return total_usable_kwh, required_storage
        if total_usable_kwh >= required_storage:
            self.log(f"Storage ready (usable {round(total_usable_kwh,1)} kWh >= required {round(required_storage,1)} kWh)")
            self.log(f"Maximum required SWT during the next onpeak: {round(self.rwt(0, return_rswt_onpeak=True),2)} F")
            # self.log(f"Max storage available (~ all layers are at 170F): {}")
            self.storage_declared_ready = True
            return True
        else:
            if H0N.store_cold_pipe in self.latest_temperatures:
                self.log(f"Store cold pipe: {round(self.to_fahrenheit(self.latest_temperatures[H0N.store_cold_pipe]/1000),1)} F")
                if self.to_fahrenheit(self.latest_temperatures[H0N.store_cold_pipe]/1000) > self.params.MaxEwtF:
                    self.log(f"The storage is not ready, but the bottom is above the maximum EWT ({self.params.MaxEwtF} F).")
                    self.log("The storage will therefore be considered ready, as we cannot charge it further.")
                    self.full_storage_energy = total_usable_kwh
                    self.storage_declared_ready = True
                    return True
            self.log(f"Storage not ready (usable {round(total_usable_kwh,1)} kWh < required {round(required_storage,1)} kWh)")
            self.log(f"Max required SWT during the next onpeak: {round(self.rwt(0, return_rswt_onpeak=True),2)} F")
            # self.log(f"Max storage available (~ all layers are at 170F): {}")
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
        if self.cn.tank[1].depth1 in self.latest_temperatures: # TODO: this will always be true since we are filling missing temperatures
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
    
    def to_celcius(self, t: float) -> float:
        return (t-32)*5/9

    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32

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
