import asyncio
from typing import Any, Sequence
from enum import auto
import uuid
import requests
import time
import numpy as np
import dotenv
from datetime import datetime, timedelta
import pytz
from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface,  MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from result import Ok, Result
from gwproto.message import Header
from transitions import Machine
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import (ChangeRelayState, ChangeHeatPumpControl, ChangeAquastatControl, 
                           ChangeStoreFlowRelay, FsmReportType, MainAutoState)
from gwproto.named_types import (FsmEvent, MachineStates, FsmAtomicReport,
                                 FsmFullReport, ScadaParams)
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
        self.dotenv_filepath = dotenv.find_dotenv()
        self._stop_requested: bool = False
        self.main_loop_sleep_seconds = 60
        self.hardware_layout = self._services.hardware_layout
        self.temperature_channel_names = [
            'buffer-depth1', 'buffer-depth2', 'buffer-depth3', 'buffer-depth4', 
            'tank1-depth1', 'tank1-depth2', 'tank1-depth3', 'tank1-depth4', 
            'tank2-depth1', 'tank2-depth2', 'tank2-depth3', 'tank2-depth4', 
            'tank3-depth1', 'tank3-depth2', 'tank3-depth3', 'tank3-depth4',
            'hp-ewt', 'hp-lwt', 'dist-swt', 'dist-rwt', 
            'buffer-cold-pipe', 'buffer-hot-pipe', 'store-cold-pipe', 'store-hot-pipe',
            ]
        self.temperatures_available = False
        self.storage_declared_ready = False
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
        # House parameters in the .env file
        self.is_simulated = self.settings.is_simulated
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.latitude = self.settings.latitude
        self.longitude = self.settings.longitude
        self.alpha = self.settings.alpha
        self.beta = self.settings.beta
        self.gamma = self.settings.gamma
        self.hp_max_kw_th = self.settings.hp_max_kw_th
        self.no_power_rswt = self.settings.no_power_rswt
        self.intermediate_power = self.settings.intermediate_power
        self.intermediate_rswt = self.settings.intermediate_rswt
        self.dd_power = self.settings.dd_power
        self.dd_rswt = self.settings.dd_rswt
        self.dd_delta_t = self.settings.dd_delta_t
        self.log(f"self.timezone: {self.timezone}")
        self.log(f"self.latitude: {self.latitude}")
        self.log(f"self.longitude: {self.longitude}")
        self.log(f"self.alpha: {self.alpha}")
        self.log(f"self.beta: {self.beta}")
        self.log(f"self.gamma: {self.gamma}")
        self.log(f"self.hp_max_kw_th: {self.hp_max_kw_th}")
        self.log(f"self.no_power_rswt: {self.no_power_rswt}")
        self.log(f"self.intermediate_power: {self.intermediate_power}")
        self.log(f"self.intermediate_rswt: {self.intermediate_rswt}")
        self.log(f"self.dd_power: {self.dd_power}")
        self.log(f"self.dd_rswt: {self.dd_rswt}")
        self.log(f"self.dd_delta_t: {self.dd_delta_t}")
        self.log(f"self.is_simulated: {self.is_simulated}")
        # Find the quadratic function that finds heating power from RSWT
        x_rswt = np.array([self.no_power_rswt, self.intermediate_rswt, self.dd_rswt])
        y_hpower = np.array([0, self.intermediate_power, self.dd_power])
        A = np.vstack([x_rswt**2, x_rswt, np.ones_like(x_rswt)]).T
        self.rswt_quadratic_params = np.linalg.solve(A, y_hpower)
        self.log(f"self.rswt_quadratic_params: {self.rswt_quadratic_params}")
        # Get the weather forecast
        self.weather = None
        self.weather_long = None
        self.get_weather()

    def trigger_event(self, event: HomeAloneEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        self.log(f"{event}: {orig_state} -> {self.state}")
        self._send_to(
            self.services._layout.nodes[H0N.primary_scada],
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
        self._send_to(self.services._layout.nodes[H0N.primary_scada],
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
        return [MonitoredName(self.name, 300)]
        #return [MonitoredName(self.name, self.main_loop_sleep_seconds * 2.1)]

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
                        else:
                            self.trigger_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady.value)
                    
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
                            if self.storage_declared_ready:
                                self.log("The storage was already declared ready during this off-peak period")
                            else:
                                self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)

                elif self.state==HomeAloneState.HpOffStoreDischarge.value:
                    if not self.is_onpeak():
                        self.trigger_event(HomeAloneEvent.OffPeakStart.value)
                    elif self.is_buffer_full() or self.is_storage_colder_than_buffer():
                        self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)

                if self.state != previous_state:                    
                    self.update_relays(previous_state)

            await asyncio.sleep(self.main_loop_sleep_seconds)

    def update_relays(self, previous_state):
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
        
    def _turn_on_HP(self):
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

    def _turn_off_HP(self):
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

    def _turn_on_store(self):
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


    def _turn_off_store(self):
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


    def _valved_to_charge_store(self):
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

    def _valved_to_discharge_store(self):
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
            case ScadaParams():
                self._process_scada_params(message.Payload)
        return Ok(True)
    
    def update_env_variable(self, variable, new_value):
        if not self.dotenv_filepath:
            self.log("Couldn't find a .env file!")
            return
        with open(self.dotenv_filepath, 'r') as file:
            lines = file.readlines()
        with open(self.dotenv_filepath, 'w') as file:
            for line in lines:
                if line.startswith(f"{variable}="):
                    file.write(f"{variable}={new_value}\n")
                else:
                    file.write(line)

    def _process_scada_params(self, message: ScadaParams) -> None:
        self.log("Got ScadaParams - check h.latest")
        self.latest = message
        # if hasattr(message, "SwtColdestHr"):
        #     old = self.swt_coldest_hour
        #     self.swt_coldest_hour = message.SwtColdestHr
        #     self.update_env_variable('SCADA_SWT_COLDEST_HOUR', self.swt_coldest_hour)
        #     response = ScadaParams(
        #         FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
        #         FromName=self.name,
        #         ToName=message.FromName,
        #         UnixTimeMs=int(time.time() * 1000),
        #         MessageId=message.MessageId,
        #         OldSwtColdestHr=old,
        #         NewSwtColdestHr=self.swt_coldest_hour
        #     )
        #     self.log(f"Sending back {response}")
        #     self.send_to_atn(response)
        # if hasattr(message, "AveragePowerColdestHourKw"):
        #     old = self.average_power_coldest_hour_kw
        #     self.average_power_coldest_hour_kw = message.AveragePowerColdestHourKw
        #     self.update_env_variable('SCADA_AVERAGE_POWER_COLDEST_HOUR_KW', self.average_power_coldest_hour_kw)
        #     response = ScadaParams(
        #         FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
        #         FromName=self.name,
        #         ToName=message.FromName,
        #         UnixTimeMs=int(time.time() * 1000),
        #         MessageId=message.MessageId,
        #         OldAveragePowerColdestHourKw=old,
        #         NewAveragePowerColdestHourKw=self.average_power_coldest_hour_kw
        #     )
        #     self.log(f"Sending back {response}")
        #     self.send_to_atn(response)
        # if hasattr(message, "BufferEmpty"):
        #     old = self.buffer_empty
        #     self.buffer_empty = message.BufferEmpty
        #     self.update_env_variable('SCADA_BUFFER_EMPTY', self.buffer_empty)
        #     response = ScadaParams(
        #         FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
        #         FromName=self.name,
        #         ToName=message.FromName,
        #         UnixTimeMs=int(time.time() * 1000),
        #         MessageId=message.MessageId,
        #         OldBufferEmpty=old,
        #         NewBufferEmpty=self.buffer_empty
        #     )
        #     self.log(f"Sending back {response}")
        #     self.send_to_atn(response)
        # if hasattr(message, "BufferFull"):
        #     old = self.buffer_full
        #     self.buffer_full = message.BufferFull
        #     self.update_env_variable('SCADA_BUFFER_FULL', self.buffer_full)
        #     response = ScadaParams(
        #         FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
        #         FromName=self.name,
        #         ToName=message.FromName,
        #         UnixTimeMs=int(time.time() * 1000),
        #         MessageId=message.MessageId,
        #         OldBufferFull=old,
        #         NewBufferFull=self.buffer_full
        #     )
        #     self.log(f"Sending back {response}")
        #     self.send_to_atn(response)

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
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) < 60 # TODO: improve conditions
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) > 200):
                self.latest_temperatures[layer] = None
        if 'store-cold-pipe' in self.latest_temperatures:
            value_below = self.latest_temperatures['store-cold-pipe']
        else:
            value_below = 0
        for layer in sorted(all_store_layers, reverse=True):
            if self.latest_temperatures[layer] is None:
                self.latest_temperatures[layer] = value_below
            value_below = self.latest_temperatures[layer]  
        self.latest_temperatures = {k:self.latest_temperatures[k] for k in sorted(self.latest_temperatures)}

    def get_latest_temperatures(self):
        self.latest_temperatures = {
            x: self.services._data.latest_channel_values[x] 
            for x in self.temperature_channel_names
            if x in self.services._data.latest_channel_values
            and self.services._data.latest_channel_values[x] is not None
            }
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
            print('Temperatures available')
        else:
            self.temperatures_available = False
            print('Some temperatures are missing')
            all_buffer = [x for x in self.temperature_channel_names if 'buffer-depth' in x]
            available_buffer = [x for x in list(self.latest_temperatures.keys()) if 'buffer-depth' in x]
            if all_buffer == available_buffer:
                print("But all the buffer temperatures are available")
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
        if ((time_now.hour in peak_hours or time_in_2min.hour in peak_hours)
            and time_now.weekday() < 5):
            self.log("On-peak")
            return True
        else:
            self.log("Not on-peak")
            return False

    def is_buffer_empty(self) -> bool:
        if 'buffer-depth1' in self.latest_temperatures:
            buffer_empty_temp = 'buffer-depth1'
        elif 'dist-swt' in self.latest_temperatures:
            buffer_empty_temp = 'dist-swt'
        else:
            self.alert("Impossible to know if the buffer is empty!")
            return False
        max_rswt_next_3hours = max(self.weather['required_swt'][:3])
        min_buffer = max_rswt_next_3hours - self.delta_T(max_rswt_next_3hours)
        if self.latest_temperatures[buffer_empty_temp]/1000*9/5+32 < min_buffer: # TODO use to_fahrenheit()
            self.log(f"Buffer empty ({buffer_empty_temp}: {round(self.latest_temperatures[buffer_empty_temp]/1000*9/5+32,1)} < {min_buffer} F)")
            return True
        else:
            self.log(f"Buffer not empty ({buffer_empty_temp}: {round(self.latest_temperatures[buffer_empty_temp]/1000*9/5+32,1)} >= {min_buffer} F)")
            return False            
    
    def is_buffer_full(self) -> bool:
        if 'buffer-depth4' in self.latest_temperatures:
            buffer_full_temp = 'buffer-depth4'
        elif 'buffer-cold-pipe' in self.latest_temperatures:
            buffer_full_temp = 'buffer-cold-pipe'
        elif "StoreDischarge" in self.state and 'store-cold-pipe' in self.latest_temperatures:
            buffer_full_temp = 'store-cold-pipe'
        elif 'hp-ewt' in self.latest_temperatures:
            buffer_full_temp = 'hp-ewt'
        else:
            self.alert("Impossible to know if the buffer is full!")
            return False
        max_buffer = max(self.weather['required_swt'][:3])
        if self.latest_temperatures[buffer_full_temp]/1000*9/5+32 > max_buffer: # TODO use to_fahrenheit()
            self.log(f"Buffer full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)} > {max_buffer} F)")
            return True
        else:
            self.log(f"Buffer not full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)} <= {max_buffer} F)")
            return False

    def required_heating_power(self, oat, ws):
        r = self.alpha + self.beta*oat + self.gamma*ws
        return round(r,2) if r>0 else 0

    def required_swt(self,rhp):
        a, b, c = self.rswt_quadratic_params
        return round(-b/(2*a) + ((rhp-b**2/(4*a)+b**2/(2*a)-c)/a)**0.5,2)
        
    def get_weather(self):
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
            cropped_forecast = dict(list(forecasts.items())[:24])
            self.weather_long = {
                'time': list(forecasts.keys()),
                'oat': list(forecasts.values()),
                'ws': [0]*len(forecasts)
                }
            self.weather = {
                'time': list(cropped_forecast.keys()),
                'oat': list(cropped_forecast.values()),
                'ws': [0]*len(cropped_forecast)
                }
            self.log(f"Obtained a 24-hour weather forecast starting at {self.weather['time'][0]}")
        except:
            self.log("[!!] Unable to get weather forecast from API")
            if self.weather_long is None:
                self.log("No weather forecasts available! Use coldest of the current month.") # TODO
                self.weather = {
                    'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                    'oat': [30]*24,
                    'ws': [0]*24,
                    }
            else: 
                if self.weather_long['time'][-1] >= time.time()+timedelta(hours=24):
                    self.log("Some weather forecast is available, but it is not the most recent")
                    time_late = datetime.now(self.timezone) - self.weather_long['time'][0]
                    hours_late = int(time_late.total_seconds()/3600)
                    self.weather = dict(list(self.weather_long.items())[hours_late:hours_late+24])
                # TODO: fill in missing weather if not 24 hours of forecast available
                else:
                    self.log("No weather forecasts available! Use coldest of the current month.") # TODO
                    self.weather = {
                        'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                        'oat': [30]*24,
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
       
    def get_required_storage(self, time_now):
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
        if (((time_now.weekday()<4 or time_now.weekday()==6) and time_now.hour>=20)
            or (time_now.weekday()<5 and time_now.hour<=6)):
            self.log('Preparing for a morning onpeak + afternoon onpeak')
            afternoon_missing_kWh = afternoon_kWh - (4*self.hp_max_kw_th - midday_kWh)
            return morning_kWh if afternoon_missing_kWh<0 else morning_kWh + afternoon_missing_kWh
        elif (time_now.weekday()<5 and time_now.hour>=12 and time_now.hour<16):
            self.log('Preparing for an afternoon onpeak')
            return afternoon_kWh
        else:
            self.log('No onpeak period coming up soon')
            return 0

    def is_storage_ready(self) -> bool:
        time_now = datetime.now(self.timezone)
        latest_temperatures = self.latest_temperatures.copy()
        storage_temperatures = {k:v for k,v in latest_temperatures.items() if 'tank' in k}
        simulated_layers = [self.to_fahrenheit(v/1000) for k,v in storage_temperatures.items()]        
        total_usable_kwh = 0
        while True:
            if round(self.rwt(simulated_layers[0],time_now)) == round(simulated_layers[0]):
                simulated_layers = [sum(simulated_layers)/len(simulated_layers) for x in simulated_layers]
                if round(self.rwt(simulated_layers[0],time_now)) == round(simulated_layers[0]):
                    break
            total_usable_kwh += 360/12*3.78541 * 4.187/3600 * (simulated_layers[0]-self.rwt(simulated_layers[0],time_now))*5/9
            simulated_layers = simulated_layers[1:] + [self.rwt(simulated_layers[0],time_now)]        
        required_storage = self.get_required_storage(time_now)
        if total_usable_kwh >= required_storage:
            self.log(f"Storage ready (usable {round(total_usable_kwh,1)} kWh >= required {round(required_storage,1)} kWh)")
            self.storage_declared_ready = time.time()
            return True
        else:
            self.log(f"Storage not ready (usable {round(total_usable_kwh,1)} kWh < required {round(required_storage,1)}) kWh)")
            return False
        
    def is_storage_colder_than_buffer(self) -> bool:
        if 'buffer-depth1' in self.latest_temperatures:
            buffer_top = 'buffer-depth1'
        elif 'buffer-depth2' in self.latest_temperatures:
            buffer_top = 'buffer-depth2'
        elif 'buffer-depth3' in self.latest_temperatures:
            buffer_top = 'buffer-depth3'
        elif 'buffer-depth4' in self.latest_temperatures:
            buffer_top = 'buffer-depth4'
        elif 'buffer-cold-pipe' in self.latest_temperatures:
            buffer_top = 'buffer-cold-pipe'
        else:
            self.alert("It is impossible to know if the top of the buffer is warmer than the top of the storage!")
            return False
        if 'tank1-depth1' in self.latest_temperatures: # TODO: this will always be true since we are filling missing temperatures
            tank_top = 'tank1-depth1'
        elif 'store-hot-pipe' in self.latest_temperatures:
            tank_top = 'store-hot-pipe'
        elif 'buffer-hot-pipe' in self.latest_temperatures:
            tank_top = 'buffer-hot-pipe'
        else:
            self.alert("It is impossible to know if the top of the storage is warmer than the top of the buffer!")
            return False
        if self.latest_temperatures[buffer_top] > self.latest_temperatures[tank_top]:
            self.log("Storage top colder than buffer top")
            return True
        else:
            print("Storage top warmer than buffer top")
            return False
    
    def to_celcius(self, t):
        return (t-32)*5/9

    def to_fahrenheit(self, t):
        return t*9/5+32

    def delta_T(self, swt):
        a, b, c = self.rswt_quadratic_params
        delivered_heat_power = a*swt**2 + b*swt + c
        d = self.dd_delta_t/self.dd_power * delivered_heat_power
        return d if d>0 else 0
    
    def rwt(self, swt, timenow):
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
        if swt < required_swt - 10:
            delta_t = 0
        elif swt < required_swt:
            delta_t = self.delta_T(required_swt) * (swt-(required_swt-10))/10
        else:
            delta_t = self.delta_T(swt)
        return round(swt - delta_t,2)
    
    def _send_to(self, dst: ShNode, payload) -> None:
        if (
                dst.name == self.services.name or
                self.services.get_communicator(dst.name) is not None
        ):
            self._send(
                Message(
                    header=Header(
                        Src=self.name,
                        Dst=dst.name,
                        MessageType=payload.TypeName,
                    ),
                    Payload=payload,
                )
            )
        else:
            # Otherwise send via local mqtt
            message = Message(Src=self.name, Dst=dst.name, Payload=payload)
            return self.services.publish_message( # noqa
                self.services.LOCAL_MQTT, # noqa
                message,
                qos=QOS.AtMostOnce,
            )

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)
        print(log_str)

    def alert(self, msg) -> None:
        alert_str = f"[ALERT] {msg}"
        self.log(alert_str)
        # TODO: send Opsgenie alert

    def send_to_atn(self, payload: Any) -> None:
        self._services._links.publish_upstream(payload)
# if __name__ == '__main__':
#     from actors import HomeAlone; from command_line_utils import get_scada; s=get_scada(); s.run_in_thread(); h: HomeAlone = s.get_communicator('h')