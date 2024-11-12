import asyncio
from enum import auto
import uuid
import time
from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface, Problems
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from result import Err, Ok, Result
from gwproto.message import Header
from transitions import Machine
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import ChangeRelayState
from gwproto.named_types import FsmEvent, MachineStates
import pendulum


class HomeAloneState(GwStrEnum):
    WaitingForTemperaturesOnPeak = auto()
    WaitingForTemperaturesOffPeak = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()


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
        "home.alone.event"


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
        self._stop_requested: bool = False
        self.hardware_layout = self._services.hardware_layout
        self.datachannels = list(self.hardware_layout.data_channels.values())
        self.temperature_channel_names = [
            'buffer-depth1', 'buffer-depth2', 'buffer-depth3', 'buffer-depth4', 
            'tank1-depth1', 'tank1-depth2', 'tank1-depth3', 'tank1-depth4', 
            'tank2-depth1', 'tank2-depth2', 'tank2-depth3', 'tank2-depth4', 
            'tank3-depth1', 'tank3-depth2', 'tank3-depth3', 'tank3-depth4',
            ]
        self.temperatures_available = False
        self.hp_onoff_relay = self.hardware_layout.node(H0N.hp_scada_ops_relay)
        self.hp_failsafe_relay = self.hardware_layout.node(H0N.hp_failsafe_relay)
        self.store_pump_onoff_relay = self.hardware_layout.node(H0N.store_pump_failsafe)
        self.store_charge_discharge_relay = self.hardware_layout.node(H0N.store_charge_discharge_relay)
        self.initialize_relays()
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=HomeAloneState.WaitingForTemperaturesOnPeak.value,
            send_event=True,
        )
        # House parameters
        self.average_power_coldest_hour_kW = 5 # TODO
        self.swt_coldest_hour = 140 # TODO
        self.temp_drop_function = [20,0] #TODO
        # In simulation vs in a real house
        self.simulation = False


    def trigger_event(self, event: HomeAloneEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        # self._send_to(
        #     self.services._layout.nodes[H0N.primary_scada],
        #     MachineStates(
        #         MachineHandle=self.node.handle,
        #         StateEnum=HomeAloneEvent.enum_name(),
        #         StateList=[self.state],
        #         UnixMsList=[now_ms],
        #     ),
        # )
        self.services.logger.error(
            f"[{self.name}] {event}: {orig_state} -> {self.state}"
        )


    async def main(self):
        
        while not self._stop_requested:
    
            previous_state = self.state
            print(f"\nNow in {previous_state}")

            self.get_latest_temperatures()

            if (self.state==HomeAloneState.WaitingForTemperaturesOnPeak 
                or self.state==HomeAloneState.WaitingForTemperaturesOffPeak):
                if self.temperatures_available:
                    print('Temperatures available')
                    if self.is_onpeak():
                        if self.is_buffer_empty():
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
                        self.trigger_event(HomeAloneEvent.OnPeakBufferEmpty.value)
                else:
                    if self.is_buffer_empty():
                        self.trigger_event(HomeAloneEvent.OffPeakBufferEmpty.value)
                    elif self.is_storage_ready():
                        self.trigger_event(HomeAloneEvent.OffPeakStorageNotReady.value)

            elif self.state==HomeAloneState.HpOffStoreDischarge.value:
                if not self.is_onpeak():
                    self.trigger_event(HomeAloneEvent.OffPeakStart.value)
                elif self.is_buffer_full():
                    self.trigger_event(HomeAloneEvent.OnPeakBufferFull.value)

            if self.state != previous_state:                    
                self.update_relays(previous_state)
            await asyncio.sleep(10)


    def update_relays(self, previous_state):
        if self.state==HomeAloneState.WaitingForTemperaturesOnPeak.value:
            self._turn_off_HP()
        if "HpOn" not in previous_state and "HpOn" in self.state:
            self._turn_on_HP()
        if "HpOff" not in previous_state and "HpOff" in self.state:
            self._turn_off_HP()
        if "StoreOff" not in previous_state and "StoreOff" in self.state:
            self._turn_off_store()
        if "StoreCharge" not in previous_state and "StoreCharge" in self.state:
            if "StoreCharge" not in previous_state and "StoreDischarge" not in previous_state:
                self._turn_on_store()
            self._charge_store()
        if "StoreDischarge" not in previous_state and "StoreDischarge" in self.state:
            if "StoreCharge" not in previous_state and "StoreDischarge" not in previous_state:
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


    def change_all_temps(self, temp_c) -> None:
        if self.simulation:
            for channel_name in self.temperature_channel_names:
                self.change_temp(channel_name, temp_c)
        else:
            print("This function is only available in simulation")


    def change_temp(self, channel_name, temp_c) -> None:
        if self.simulation:
            self.services._data.latest_channel_values[self.get_datachannel(channel_name)] = temp_c * 1000
        else:
            print("This function is only available in simulation")


    def get_latest_temperatures(self):
        self.latest_temperatures = {
            x: self.services._data.latest_channel_values[self.get_datachannel(x)] 
            for x in self.temperature_channel_names
            if self.get_datachannel(x) in self.services._data.latest_channel_values
            and self.services._data.latest_channel_values[self.get_datachannel(x)] is not None
            }
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
        else:
            self.temperatures_available = False
            print('Some temperatures are missing')
            

    def get_datachannel(self, name):
        for dc in self.datachannels:
            if name in dc.Name:
                return dc
        return None
    

    def initialize_relays(self):
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.hp_failsafe_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            SendTimeUnixMs=int(time.time()*1000),
            TriggerId=str(uuid.uuid4()),
            )
        self._send_to(self.hp_failsafe_relay, event)
        self.services.logger.error(f"{self.node.handle} sending CloseRelay to {self.hp_failsafe_relay.name}")


    def is_onpeak(self):
        time_now = pendulum.now(tz="America/New_York")
        time_in_2min = pendulum.now(tz="America/New_York").add(minutes=2)
        peak_hours = [8,9,10,11] + [16,17,18,19]
        if ((time_now.hour in peak_hours or time_in_2min.hour in peak_hours) 
            and time_now.day_of_week < 5):
            print("On-peak")
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
            print(f"Storage ready (usable {round(total_usable_kwh,1)} kWh >= required {round(required_storage,1)} kWh")
            return True
        else:
            print(f"Storage not ready (usable {round(total_usable_kwh,1)} kWh < required {round(required_storage,1)}) kWh")
            return False
        
    
    def temp_drop(self, T):
        intercept, coeff = self.temp_drop_function
        return intercept + coeff*T
    

    def _send_to(self, dst: ShNode, payload) -> None:
        if dst.name in set(self.services._communicators.keys()) | {self.services.name}:
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
            return self.services._links.publish_message(
                self.services.LOCAL_MQTT, message, qos=QOS.AtMostOnce
            )


# if __name__ == '__main__':
#     from actors import HomeAlone; from command_line_utils import get_scada; s=get_scada(); s.run_in_thread(); h: HomeAlone = s.get_communicator('h')