import asyncio
from enum import auto
from time import time
import uuid
from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface, Problems
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from result import Err, Ok, Result
from transitions import Machine
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.enums import (ActorClass, ChangeRelayState,
                           FsmReportType, PicoCyclerState)
from gwproto.named_types import (ChannelReadings, FsmAtomicReport, FsmEvent,
                                 FsmFullReport)
import pendulum


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

class HomeAlone(Actor):
    
    states = [
        "HpOnStoreOff",
        "HpOnStoreCharge",
        "HpOffStoreOff",
        "HpOffStoreDischarge",
    ]

    transitions = [
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
        self._stop_requested: bool = False
        self.initialized = False
        self.hardware_layout = self._services.hardware_layout
        self.datachannels = list(self.hardware_layout.data_channels.values())
        self.temperature_channel_names = [
            'buffer-depth1', 'buffer-depth2', 'buffer-depth3', 'buffer-depth4', 
            'tank1-depth1', 'tank1-depth2', 'tank1-depth3', 'tank1-depth4', 
            'tank2-depth1', 'tank2-depth2', 'tank2-depth3', 'tank2-depth4', 
            'tank3-depth1', 'tank3-depth2', 'tank3-depth3', 'tank3-depth4',
            ]
        asyncio.sleep(60)
        self.get_latest_temperatures()
        self.hp_onoff_relay = self.hardware_layout.node(H0N.hp_scada_ops_relay)
        self.hp_failsafe_relay = self.hardware_layout.node(H0N.hp_failsafe_relay)
        self.store_pump_onoff_relay = self.hardware_layout.node(H0N.store_pump_failsafe)
        self.store_charge_discharge_relay = self.hardware_layout.node(H0N.store_charge_discharge_relay)
        # House parameters
        self.average_power_coldest_hour_kW = 5 # TODO
        self.swt_coldest_hour = 140 # TODO
        self.temp_drop_function = [20,0] #TODO


    async def main(self):
        
        while not self._stop_requested:

            if not self.initialized:
                await asyncio.sleep(2)
                self.initialize()  
            
            await asyncio.sleep(60)
    
            self.get_latest_temperatures()

            previous_state = self.state
            print(f"\nNow in {previous_state}")

            if self.state=="HpOnStoreOff":
                if self.is_onpeak():
                    self.trigger(HomeAloneEvent.OnPeakStart.value)
                elif self.is_buffer_full():
                    if self.is_storage_ready():
                        self.trigger(HomeAloneEvent.OffPeakBufferFullStorageReady.value)
                    else:
                        self.trigger(HomeAloneEvent.OffPeakBufferFullStorageNotReady.value)
                
            elif self.state=="HpOnStoreCharge":
                if self.is_onpeak():
                    self.trigger(HomeAloneEvent.OnPeakStart.value)
                elif self.is_buffer_empty():
                    self.trigger(HomeAloneEvent.OffPeakBufferEmpty.value)
                elif self.is_storage_ready():
                    self.trigger(HomeAloneEvent.OffPeakStorageReady.value)
                
            elif self.state=="HpOffStoreOff":
                if self.is_onpeak():
                    if self.is_buffer_empty():
                        self.trigger(HomeAloneEvent.OnPeakBufferEmpty.value)
                else:
                    if self.is_buffer_empty():
                        self.trigger(HomeAloneEvent.OffPeakBufferEmpty.value)
                    elif self.is_storage_ready():
                        self.trigger(HomeAloneEvent.OffPeakStorageNotReady.value)

            elif self.state=="HpOffStoreDischarge":
                if not self.is_onpeak():
                    self.trigger(HomeAloneEvent.OffPeakStart.value)
                elif self.is_buffer_full():
                    self.trigger(HomeAloneEvent.OnPeakBufferFull.value)

            if self.state != previous_state:
                self.switch_relays(previous_state)


    def switch_relays(self, previous_state):
        print(f"Moving to {self.state}:")
        if "HpOff" in previous_state and "HpOn" in self.state:
            self._turn_on_HP()
        if "HpOn" in previous_state and "HpOff" in self.state:
            self._turn_off_HP()
        if "StoreOff" not in previous_state and "StoreOff" in self.state:
            self._turn_off_store()
        if "StoreCharge" not in previous_state and "StoreCharge" in self.state:
            if "StoreOff" in previous_state:
                self._turn_on_store()
            self._charge_store()
        if "StoreDischarge" not in previous_state and "StoreDischarge" in self.state:
            if "StoreOff" in previous_state:
                self._turn_on_store()
            self._discharge_store()


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
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to {self.hp_onoff_relay.name}")


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
        self.services.logger.error(f"{self.node.handle} sending OpenRelay to {self.hp_onoff_relay.name}")


    def _turn_on_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending OpenRelay to {self.store_pump_onoff_relay.name}")
    

    def _turn_off_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_pump_onoff_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_pump_onoff_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to {self.store_pump_onoff_relay.name}")


    def _charge_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_charge_discharge_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_charge_discharge_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to {self.store_charge_discharge_relay.name}")


    def _discharge_store(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.store_charge_discharge_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.store_charge_discharge_relay, event)
        self.services.logger.error(f"{self.node.handle} sending OpenRelay to {self.store_charge_discharge_relay.name}")


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


    def get_latest_temperatures(self):
        self.latest_temperatures = {
            x: self.services._data.latest_channel_values[self.get_datachannel(x)] 
            for x in self.temperature_channel_names
            if self.get_datachannel(x) in self.services._data.latest_channel_values
            }
        if self.latest_temperatures.keys() != self.temperature_channel_names:

            raise ValueError('Some temperatures are missing!')
            # TODO: remove temporary solution
            # self.latest_temperatures = {
            #     x: 65000
            #     for x in self.temperature_channel_names
            #     }
            

    def get_datachannel(self, name):
        for dc in self.datachannels:
            if name in dc.Name:
                return dc
        return None


    def initialize(self) -> None:
        print("\nInitializing...")
        if self.is_onpeak():
            if self.is_buffer_empty():
                initial_state = "HpOffStoreDischarge"
            else:
                initial_state = "HpOffStoreOff"
        else:
            if self.is_buffer_empty():
                initial_state = "HpOnStoreOff"
            else:
                if self.is_storage_ready():
                    initial_state = "HpOffStoreOff"
                else:
                    initial_state = "HpOnStoreCharge"
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=initial_state,
            send_event=True,
        )
        print(f"=> Initialize to {self.state}")
        self.initialize_relays()
        self.initialized = True


    def initialize_relays(self):

        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_failsafe_relay.handle,
            EventType=ChangeRelayState.enum_name,
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_failsafe_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to {self.hp_failsafe_relay.name}")

        if "HpOn" in self.state:
            self._turn_on_HP()
        if "HpOff" in self.state:
            self._turn_off_HP()
        if "StoreOff" in self.state:
            self._turn_off_store()
        if "StoreCharge" in self.state:
            self._charge_store()
        if "StoreOff" in self.state:
            self._discharge_store()


    def is_onpeak(self):
        time_now = pendulum.now(tz="America/New_York")
        time_in_2min = pendulum.now(tz="America/New_York").add(minutes=2)
        peak_hours = [8,9,10,11] + [16,17,18,19]
        if ((time_now.hour in peak_hours or time_in_2min.hour in peak_hours) 
            and time_now.day_of_week < 5):
            print("On-peak (or soon to be on-peak)")
            return True
        else:
            print("Not on-peak")
            return False


    def is_buffer_empty(self):
        if self.latest_temperatures['buffer-depth2'] < self.swt_coldest_hour:
            print("Buffer empty")
            return True
        else:
            print("Buffer not empty")
            return False
        
    
    def is_buffer_full(self):
        if self.latest_temperatures['buffer-depth4'] > self.swt_coldest_hour:
            print("Buffer full")
            return True
        else:
            print("Buffer not full")
            return False
        

    def is_storage_ready(self):
        total_usable_kwh = 0
        for layer in [x for x in self.latest_temperatures.keys() if 'tank' in x]:
            layer_temp_f = self.latest_temperatures[layer]/1000*9/5+32
            if layer_temp_f > self.swt_coldest_hour:
                layer_energy_kwh = 360/4*3.78541 * 4.187/3600 * self.temp_drop(layer_temp_f)*5/9
                total_usable_kwh += layer_energy_kwh
        time_now = pendulum.now(tz="America/New_York")
        if time_now.hour in [20,21,22,23,0,1,2,3,4,5,6,7]:
            required_storage = 7.5*self.average_power_coldest_hour_kW
        else:
            required_storage = 4*self.average_power_coldest_hour_kW
        if total_usable_kwh >= required_storage:
            print(f"Storage ready (usable {round(total_usable_kwh,1)} >= required {round(required_storage,1)})")
            return True
        else:
            print(f"Storage not ready (usable {round(total_usable_kwh,1)} < required {round(required_storage,1)})")
            return False
        
    
    def temp_drop(self, T):
        intercept, coeff = self.temp_drop_function
        return intercept + coeff*T


# if __name__ == '__main__':
#     from actors import HomeAlone; from command_line_utils import get_scada; s=get_scada(); s.run_in_thread(); h: HomeAlone = s.get_communicator('h')