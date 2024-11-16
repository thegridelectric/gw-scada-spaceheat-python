import asyncio
from typing import Sequence
from enum import auto
import uuid
import time
from datetime import datetime, timedelta
import pytz
from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface,  MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from result import  Result
from gwproto.message import Header
from transitions import Machine
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import (ChangeRelayState, ChangeHeatPumpControl, ChangeAquastatControl, 
                           ChangeStoreFlowRelay, FsmReportType)
from gwproto.named_types import FsmEvent, MachineStates, FsmAtomicReport, FsmFullReport
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
        self._stop_requested: bool = False
        self.hardware_layout = self._services.hardware_layout
        self.datachannels = list(self.hardware_layout.data_channels.values())
        self.temperature_channel_names = [
            'buffer-depth1', 'buffer-depth2', 'buffer-depth3', 'buffer-depth4', 
            'tank1-depth1', 'tank1-depth2', 'tank1-depth3', 'tank1-depth4', 
            'tank2-depth1', 'tank2-depth2', 'tank2-depth3', 'tank2-depth4', 
            'tank3-depth1', 'tank3-depth2', 'tank3-depth3', 'tank3-depth4',
            'hp-ewt', 'hp-lwt', 'dist-swt', 'dist-rwt', 
            'buffer-cold-pipe', 'buffer-hot-pipe', 'store-cold-pipe', 'store-hot-pipe',
            ]
        self.temperatures_available = False
        self.hp_onoff_relay: ShNode = self.hardware_layout.node(H0N.hp_scada_ops_relay)
        self.hp_failsafe_relay: ShNode = self.hardware_layout.node(H0N.hp_failsafe_relay)
        self.aquastat_ctrl_relay: ShNode = self.hardware_layout.node(H0N.aquastat_ctrl_relay)
        self.store_pump_onoff_relay: ShNode = self.hardware_layout.node(H0N.store_pump_failsafe)
        self.store_charge_discharge_relay: ShNode = self.hardware_layout.node(H0N.store_charge_discharge_relay)
        self.time_storage_declared_ready = None
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=HomeAloneState.WaitingForTemperaturesOnPeak.value,
            send_event=True,
        )
        # House parameters
        self.temp_drop_function = [20,0] #TODO
        # In simulation vs in a real house
        self.simulation = True
        self.main_loop_sleep_seconds = 60

        # Read House parameters from the .env file
        self.swt_coldest_hour = self.settings.swt_coldest_hour
        self.average_power_coldest_hour_kw = self.settings.average_power_coldest_hour_kw
        self.buffer_empty = self.settings.buffer_empty
        self.buffer_full = self.settings.buffer_full
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.log(f"self.swt_coldest_hour: {self.swt_coldest_hour}")
        self.log(f"self.average_power_coldest_hour_kw : {self.average_power_coldest_hour_kw }")
        self.log(f"self.buffer_empty: {self.buffer_empty}")
        self.log(f"self.buffer_full: {self.buffer_full}")

    def trigger_event(self, event: HomeAloneEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        self.services.logger.error(
            f"[{self.name}] {event}: {orig_state} -> {self.state}"
        )
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
        if self.is_onpeak():
            self._turn_off_HP()

        while not self._stop_requested:
            self.services.logger.error("PATTING HOME ALONE WATCHDOG")
            self.services.logger.error(f"State: {self.state}")
            self._send(PatInternalWatchdogMessage(src=self.name))
            previous_state = self.state
            print("\n"+"-"*50)
            print(f"HomeAlone state: {previous_state}")
            print("-"*50)

            if self.is_onpeak():
                self.time_storage_declared_ready = None

            self.get_latest_temperatures()

            if (self.state==HomeAloneState.WaitingForTemperaturesOnPeak 
                or self.state==HomeAloneState.WaitingForTemperaturesOffPeak):
                if self.temperatures_available:
                    print('Temperatures available')
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
                        if self.time_storage_declared_ready is not None:
                            if time.time() - self.time_storage_declared_ready > 60*60:
                                self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)
                                self.time_storage_declared_ready = None
                        else:
                            self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)

            elif self.state==HomeAloneState.HpOffStoreDischarge.value:
                if not self.is_onpeak():
                    self.trigger_event(HomeAloneEvent.OffPeakStart.value)
                elif self.is_buffer_full() or self.is_storage_colder_than_buffer():
                    self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)

            if self.state != previous_state:                    
                self.update_relays(previous_state)
            print('Done.')

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
            ToHandle=self.hp_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to Hp ScadaOps {H0N.hp_scada_ops_relay}")

    def _turn_off_HP(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending OpenRelay to Hp ScadaP[s {H0N.hp_scada_ops_relay}")

    def _turn_on_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to StorePump OnOff {H0N.store_pump_failsafe}")


    def _turn_off_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending OpenRelay to StorePump OnOff {H0N.store_pump_failsafe}")


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
        self.services.logger.error(f"{self.node.handle} sending ChargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")


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
        self.services.logger.error(f"{self.node.handle} sending DischargeStore to Store ChargeDischarge {H0N.store_charge_discharge_relay}")


    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="HomeAlone keepalive")
        )


    def stop(self) -> None:
        self._stop_requested = True
        

    async def join(self):
        ...


    def process_message(self, message: Message) -> Result[bool, BaseException]:
        ...


    def change_all_temps(self, temp_c) -> None:
        if self.simulation:
            for channel_name in self.temperature_channel_names:
                self.change_temp(channel_name, temp_c)
        else:
            print("This function is only available in simulation")


    def change_temp(self, channel_name, temp_c) -> None:
        if self.simulation:
            self.latest_temperatures[channel_name] = temp_c * 1000
        else:
            print("This function is only available in simulation")

    def fill_missing_store_temps(self):
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        for layer in all_store_layers:
            if layer not in self.latest_temperatures:
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

    def get_datachannel(self, name):
        for dc in self.datachannels:
            if name in dc.Name:
                return dc
        return None
    
    def initialize_relays(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_failsafe_relay.handle,
            EventType=ChangeHeatPumpControl.enum_name(),
            EventName=ChangeHeatPumpControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_failsafe_relay, event)
        self.services.logger.error(f"{self.node.handle} sending SwitchToScada to Hp Failsafe {H0N.hp_failsafe_relay}")

        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.aquastat_ctrl_relay.handle,
            EventType=ChangeAquastatControl.enum_name(),
            EventName=ChangeAquastatControl.SwitchToScada,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.aquastat_ctrl_relay, event)
        self.services.logger.error(f"{self.node.handle} sending SwitchToScada to Aquastat Ctrl {H0N.aquastat_ctrl_relay}")

    def is_onpeak(self) -> bool:
        time_now = datetime.now(self.timezone)
        time_in_2min = time_now + timedelta(minutes=2)
        peak_hours = [7,8,9,10,11] + [16,17,18,19]
        if (time_now.hour in peak_hours or time_in_2min.hour in peak_hours):
            # and time_now.weekday() < 5): #TODO: put this back when done testing!
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
            # TODO send an alert
            print("ALERT we can't know if the buffer is empty")
            return False

        if self.latest_temperatures[buffer_empty_temp]/1000*9/5+32 < self.buffer_empty:
            print(f"Buffer empty ({buffer_empty_temp}: {round(self.latest_temperatures[buffer_empty_temp]/1000*9/5+32,1)}F)")
            return True
        else:
            print(f"Buffer not empty ({buffer_empty_temp}: {round(self.latest_temperatures[buffer_empty_temp]/1000*9/5+32,1)}F)")
            return False            
    
    def is_buffer_full(self) -> bool:
        if 'buffer-depth4' in self.latest_temperatures:
            buffer_full_temp = 'buffer-depth4'
        else:
            if 'buffer-cold-pipe' in self.latest_temperatures:
                buffer_full_temp = 'buffer-cold-pipe'
            elif "StoreDischarge" in self.state and 'store-cold-pipe' in self.latest_temperatures:
                buffer_full_temp = 'store-cold-pipe'
            elif 'hp-ewt' in self.latest_temperatures:
                buffer_full_temp = 'hp-ewt'
            else:
                # TODO send an alert
                print("ALERT we can't know if the buffer is empty")
                return False
        
        if self.latest_temperatures[buffer_full_temp]/1000*9/5+32 > self.buffer_full:
            print(f"Buffer full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)}F)")
            return True
        else:
            print(f"Buffer not full (layer 4: {round(self.latest_temperatures[buffer_full_temp]/1000*9/5+32,1)}F)")
            return False

    def is_storage_ready(self) -> bool:
        latest_temperatures = self.latest_temperatures.copy()
        storage_temperatures = {k:v for k,v in latest_temperatures.items() if 'tank' in k}
        simulated_layers = [self.to_fahrenheit(v/1000) for k,v in storage_temperatures.items()]
        
        total_usable_kwh = 0
        while True:
            if simulated_layers[0] < self.swt_coldest_hour - 10:
                break
            total_usable_kwh += 360/12*3.78541 * 4.187/3600 * (simulated_layers[0]-self.rwt(simulated_layers[0]))*5/9
            simulated_layers = simulated_layers[1:] + [self.rwt(simulated_layers[0])]
        
        time_now = datetime.now(self.timezone)
        if time_now.hour in [20,21,22,23,0,1,2,3,4,5,6]:
            required_storage = 7.5*self.average_power_coldest_hour_kw
        else:
            required_storage = 4*self.average_power_coldest_hour_kw
        if total_usable_kwh >= required_storage:
            self.log(f"Storage ready (usable {round(total_usable_kwh,1)} kWh >= required {round(required_storage,1)} kWh)")
            self.time_storage_declared_ready = time.time()
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
            # TODO send an alert
            print("ALERT we can't know if the top of the buffer is warmer than the storage")
            return False
        if 'tank1-depth1' in self.latest_temperatures: # TODO: this will always be true since we are filling temperatures
            tank_top = 'tank1-depth1'
        elif 'store-hot-pipe' in self.latest_temperatures:
            tank_top = 'store-hot-pipe'
        elif 'buffer-hot-pipe' in self.latest_temperatures:
            tank_top = 'buffer-hot-pipe'
        else:
            # TODO send an alert
            print("ALERT we can't know if the top of the storage is warmer than the buffer")
            return False
        if self.latest_temperatures[buffer_top] > self.latest_temperatures[tank_top]:
            print("Storage top colder than buffer top")
            return True
        else:
            print("Storage top warmer than buffer top")
            return False
    
    def to_celcius(self, t):
        return round((t-32)*5/9)

    def to_fahrenheit(self, t):
        return round(t*9/5+32)
    
    def rwt(self, swt):
        if swt < self.swt_coldest_hour - 10:
            return swt
        elif swt < self.swt_coldest_hour:
            temp_drop_required_swt = (self.swt_coldest_hour-70)*0.2
            return swt - temp_drop_required_swt/10 * (swt-(self.swt_coldest_hour-10))
        else:
            temp_drop = (swt-70)*0.2
            return swt - temp_drop    
    
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

# if __name__ == '__main__':
#     from actors import HomeAlone; from command_line_utils import get_scada; s=get_scada(); s.run_in_thread(); h: HomeAlone = s.get_communicator('h')