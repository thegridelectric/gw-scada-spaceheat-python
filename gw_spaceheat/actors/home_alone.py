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
from gw.enums import GwStrEnum
from gwproactor import ServicesInterface,  MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.enums import ActorClass
from actors.scada_data import ScadaData
from actors.synth_generator import WeatherForecast
from result import Ok, Result
from transitions import Machine
from data_classes.house_0_names import H0N, H0CN
from gwproto.enums import FsmReportType
from gwproto.named_types import (Alert, MachineStates, FsmAtomicReport,
                                 FsmFullReport)

from actors.scada_actor import ScadaActor
from named_types import Ha1Params, GoDormant, WakeUp


class HomeAloneState(GwStrEnum):
    WaitingForTemperaturesOnPeak = auto()
    WaitingForTemperaturesOffPeak = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()
    Dormant = auto()

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
    GoDormant = auto()
    WakeUp = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "home.alone.event"


class HomeAlone(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60
    states = [
        "Dormant",
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
    ] + [
            {"trigger": "GoDormant", "source": state, "dest": "Dormant"}
            for state in states if state != "Dormant"
    ] + [{"trigger":"WakeUp","source": "Dormant", "dest": "WaitingForTemperaturesOnPeak"}]
    

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
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
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=HomeAloneState.WaitingForTemperaturesOnPeak.value,
            send_event=True,
        )     
        self.state: HomeAloneState = HomeAloneState.WaitingForTemperaturesOnPeak  
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.is_simulated = self.settings.is_simulated
        self.log(f"Params: {self.params}")
        self.log(f"self.is_simulated: {self.is_simulated}")
        self.weather = None
    
    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params

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

        await asyncio.sleep(5)
        self.log("INITIALIZING RELAYS")
        self.initialize_relays()

        while not self._stop_requested:
            #self.log("PATTING HOME ALONE WATCHDOG")
            self._send(PatInternalWatchdogMessage(src=self.name))

            self.log(f"State: {self.state}")
            if self.state != HomeAloneState.Dormant:                
                previous_state = self.state

                if self.is_onpeak():
                    self.storage_declared_ready = False
                    self.full_storage_energy = None

                if self.weather is None:
                    await asyncio.sleep(5)
                    continue

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
                                    self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageReady.value)
                                else:
                                    self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady.value)
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
                        else:
                            usable = self.data.latest_channel_values[H0N.usable_energy] / 1000
                            required = self.data.latest_channel_values[H0N.required_energy] / 1000
                            if usable < required:
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
                            usable = self.data.latest_channel_values[H0N.usable_energy] / 1000
                            required = self.data.latest_channel_values[H0N.required_energy] / 1000
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
            self.turn_off_HP()
        if "HpOn" not in previous_state and "HpOn" in self.state:
            self.turn_on_HP()
        if "HpOff" not in previous_state and "HpOff" in self.state:
            self.turn_off_HP()
        if "StoreDischarge" in self.state:
            self.turn_on_store_pump()
        if "StoreDischarge" not in self.state:
            self.turn_off_store_pump()
        if "StoreCharge" not in previous_state and "StoreCharge" in self.state:
            self.valved_to_charge_store()
        if "StoreCharge" in previous_state and "StoreCharge" not in self.state:
            self.valved_to_discharge_store()

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
                if self.state != HomeAloneState.Dormant:
                    self.trigger_event(HomeAloneEvent.GoDormant)
            case WakeUp():
                if self.state == HomeAloneState.Dormant:
                    # WakeUp: Dormant -> WaitingForTemperaturesOnPeak, but rename that ..
                    self.trigger_event(HomeAloneEvent.WakeUp)
                    self.initialize_relays()
            case WeatherForecast():
                self.log("Received weather forecast")
                self.weather = {
                    'time': message.Payload.Time,
                    'oat': message.Payload.OatForecast, 
                    'ws': message.Payload.WsForecast,
                    'required_swt': message.Payload.RswtForecast,
                    'avg_power': message.Payload.AvgPowerForecast,
                    'required_swt_deltaT': message.Payload.RswtDeltaTForecast,
                    }
        return Ok(True)
    
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
        self.log("IN INITIALIZATION")
        my_relays =  {
            relay
            for relay in self.layout.nodes.values()
            if relay.ActorClass == ActorClass.Relay and self.is_boss_of(relay)
        }
        for relay in my_relays - {
            self.store_charge_discharge_relay, # keep as it was
            self.hp_failsafe_relay,
            self.hp_scada_ops_relay, # keep as it was unless on peak
            self.aquastat_control_relay 
        }:
            self.de_energize(relay)
            self.log(f"JUST DE-ENERGIZED {relay.name}")
        self.hp_failsafe_switch_to_scada()
        self.aquastat_ctrl_switch_to_scada()

        if self.is_onpeak:
            self.turn_off_HP()

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
        max_deltaT_rswt_next_3_hours = max(self.weather['required_swt_deltaT'][:3])
        min_buffer = round(max_rswt_next_3hours - max_deltaT_rswt_next_3_hours,1)
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

    def is_storage_ready(self, return_missing=False) -> bool:
        total_usable_kwh = self.data.latest_channel_values[H0N.usable_energy] / 1000
        required_storage = self.data.latest_channel_values[H0N.required_energy] / 1000
        if return_missing:
            return total_usable_kwh, required_storage
        if total_usable_kwh >= required_storage:
            self.log(f"Storage ready (usable {round(total_usable_kwh,1)} kWh >= required {round(required_storage,1)} kWh)")
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
