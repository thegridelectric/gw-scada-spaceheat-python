import asyncio
from typing import Sequence
from enum import auto
import time
from datetime import datetime, timedelta
import pytz
from gw.enums import GwStrEnum
from gwproactor import ServicesInterface,  MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import ActorClass
from actors.scada_data import ScadaData
from result import Ok, Result
from transitions import Machine
from data_classes.house_0_names import H0N, H0CN

from actors.scada_actor import ScadaActor
from named_types import (
            GoDormant, Glitch, Ha1Params, 
            NewCommandTree, SingleMachineState, WakeUp, HeatingForecast)
from enums import HomeAloneTopState, LogLevel

 
class HomeAloneState(GwStrEnum):
    Initializing = auto()
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
    OnPeakHouseCold = auto()
    OnPeakStorageColderThanBuffer = auto()
    TemperaturesAvailable = auto()
    GoDormant = auto()
    WakeUp = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "home.alone.event"

class TopStateEvent(GwStrEnum):
    HouseColdOnpeak = auto()
    TopGoDormant = auto()
    TopWakeUp = auto()
    JustOffpeak = auto()
    MissingData = auto()
    DataAvailable = auto()

class HomeAlone(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60
    BLIND_MINUTES = 5
    states = [
        "Dormant",
        "Initializing",
        "HpOnStoreOff",
        "HpOnStoreCharge",
        "HpOffStoreOff",
        "HpOffStoreDischarge",
    ]

    transitions = [
        # Initializing
        {"trigger": "OnPeakBufferEmpty", "source": "Initializing", "dest": "HpOffStoreDischarge"},
        {"trigger": "OnPeakBufferFull", "source": "Initializing", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStorageColderThanBuffer", "source": "Initializing", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferEmpty", "source": "Initializing", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakBufferFullStorageReady", "source": "Initializing", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakBufferFullStorageNotReady", "source": "Initializing", "dest": "HpOnStoreCharge"},
        # Starting at: HP on, Store off ============= HP -> buffer
        {"trigger": "OffPeakBufferFullStorageNotReady", "source": "HpOnStoreOff", "dest": "HpOnStoreCharge"},
        {"trigger": "OffPeakBufferFullStorageReady", "source": "HpOnStoreOff", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStart", "source": "HpOnStoreOff", "dest": "HpOffStoreOff"},
        # Starting at: HP on, Store charging ======== HP -> storage
        {"trigger": "OffPeakBufferEmpty", "source": "HpOnStoreCharge", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakStorageReady", "source": "HpOnStoreCharge", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStart", "source": "HpOnStoreCharge", "dest": "HpOffStoreOff"},
        # Starting at: HP off, Store off ============ idle
        {"trigger": "OnPeakHouseCold", "source": "HpOffStoreOff", "dest": "HpOnStoreOff"},
        {"trigger": "OnPeakBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOffStoreDischarge"},
        {"trigger": "OffPeakBufferEmpty", "source": "HpOffStoreOff", "dest": "HpOnStoreOff"},
        {"trigger": "OffPeakStorageNotReady", "source": "HpOffStoreOff", "dest": "HpOnStoreCharge"},
        # Starting at: Hp off, Store discharging ==== Storage -> buffer
        {"trigger": "OnPeakBufferFull", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
        {"trigger": "OnPeakStorageColderThanBuffer", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
        {"trigger": "OffPeakStart", "source": "HpOffStoreDischarge", "dest": "HpOffStoreOff"},
    ] + [
            {"trigger": "GoDormant", "source": state, "dest": "Dormant"}
            for state in states if state != "Dormant"
    ] + [{"trigger":"WakeUp","source": "Dormant", "dest": "Initializing"}]
    
    top_states = ["Normal", "UsingBackupOnpeak", "Dormant", "ScadaBlind"]
    top_transitions = [
        {"trigger": "HouseColdOnpeak", "source": "Normal", "dest": "UsingBackupOnpeak"},
        {"trigger": "TopGoDormant", "source": "Normal", "dest": "Dormant"},
        {"trigger": "TopGoDormant", "source": "UsingBackupOnpeak", "dest": "Dormant"},
        {"trigger": "TopGoDormant", "source": "ScadaBlind", "dest": "Dormant"},
        {"trigger": "TopWakeUp", "source": "Dormant", "dest": "Normal"},
        {"trigger": "JustOffpeak", "source": "UsingBackupOnpeak", "dest": "Normal"},
        {"trigger": "MissingData", "source": "Normal", "dest": "ScadaBlind"},
        {"trigger": "DataAvailable", "source": "ScadaBlind", "dest": "Normal"},
    ]

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
        self.time_since_blind = None
        self.initialized_relays = False
        self.scadablind_scada = False
        self.scadablind_boiler = False
        
        self.state: HomeAloneState = HomeAloneState.Initializing  
        self.machine = Machine(
            model=self,
            states=HomeAlone.states,
            transitions=HomeAlone.transitions,
            initial=HomeAloneState.Initializing,
            send_event=True,
        )   

        self.top_state = HomeAloneTopState.Normal
        self.top_machine = Machine(
            model=self,
            states=HomeAlone.top_states,
            transitions=HomeAlone.top_transitions,
            initial=HomeAloneTopState.Normal,
            send_event=False,
            model_attribute="top_state",
        )  
        
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.is_simulated = self.settings.is_simulated
        self.oil_boiler_during_onpeak = self.settings.oil_boiler_for_onpeak_backup
        self.log(f"Params: {self.params}")
        self.log(f"self.is_simulated: {self.is_simulated}")
        self.forecasts: HeatingForecast = None
        self.zone_setpoints = {}
        if H0N.home_alone_normal not in self.layout.nodes:
            raise Exception(f"HomeAlone requires {H0N.home_alone_normal} node!!")
        if H0N.home_alone_scada_blind not in self.layout.nodes:
            raise Exception(f"HomeAlone requires {H0N.home_alone_scada_blind} node!!")
        if H0N.home_alone_onpeak_backup not in self.layout.nodes:
            raise Exception(f"HomeAlone requires {H0N.home_alone_onpeak_backup} node!!")

    @property
    def normal_node(self) -> ShNode:
        """
        Overwrite the standard 
        """
        return self.layout.node(H0N.home_alone_normal)

    @property
    def onpeak_backup_node(self) -> ShNode:
        """ 
        The node / state machine responsible
        for onpeak backup operations
        """
        return self.layout.node(H0N.home_alone_onpeak_backup)

    @property
    def scada_blind_node(self) -> ShNode:
        """
        THe node / state machine responsible
        for when the scada has missing data (forecasts / temperatures)
        """
        return self.layout.node(H0N.home_alone_scada_blind)

    @property
    def data(self) -> ScadaData:
        return self._services.data

    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params

    def trigger_normal_event(self, event: HomeAloneEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        self.log(f"{event}: {orig_state} -> {self.state}")
        self._send_to(
            self.primary_scada,
            SingleMachineState(
                MachineHandle=self.normal_node.handle,
                StateEnum=HomeAloneState.enum_name(),
                State=self.state,
                UnixMs=now_ms,
                Cause=event
            )
        )

    def set_onpeak_backup_command_tree(self) -> None:
        for node in self.my_actuators():
            node.Handle = f"{H0N.auto}.{H0N.home_alone}.{H0N.home_alone_onpeak_backup}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )

    def set_normal_command_tree(self) -> None:
        for node in self.my_actuators():
            node.Handle =  f"{H0N.auto}.{H0N.home_alone}.{H0N.home_alone_normal}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )
        self.log("Set normal command tree")

    def set_scadablind_command_tree(self) -> None:
        for node in self.my_actuators():
            node.Handle = f"{H0N.auto}.{H0N.home_alone}.{H0N.home_alone_scada_blind}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )
        self.log("Set scadablind command tree")

    def top_state_update(self, cause: TopStateEvent) -> None:
        """
        Report top state associated to node "h"
        """
        now_ms = int(time.time() * 1000)
        self._send_to(
            self.primary_scada,
            SingleMachineState(
                MachineHandle=self.node.handle,
                StateEnum=HomeAloneTopState.enum_name(),
                State=self.top_state,
                UnixMs=now_ms,
                Cause=cause.value,
            ),
        )
        self.log("Set top state command tree")


    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.MAIN_LOOP_SLEEP_SECONDS * 2.1)]
    
    def house_is_cold_onpeak(self) -> bool:
        if self.is_onpeak() and self.is_house_cold():
            return True
        return False
    
    def trigger_house_cold_onpeak_event(self) -> None:
        """
        Called to change top state from Normal to HouseColdOnpeak. Only acts if
          (a) house is actually cold onpeak and (b) top state is Normal
        What it does: 
          - changes command tree (all relays will be direct reports of auto.h.onpeak-backup)
          - triggers HouseColdOnpeak
          - takes necessary actuator actions to go onpeak
          - updates the normal state to Dormant if needed
          - reports top state change

        """
        # if not self.house_is_cold_onpeak():
        #     self.log("Not triggering HouseColdOnpeak top event -  house is not cold onpeak!")
        #     return
        # if not self.top_state == HomeAloneTopState.Normal:
        #     self.log("Not triggering HouseColdOnpeak top event - not in top state Normal!")
        #     return
        # implement the change in command tree. Boss: h.n -> h.onpeak-backup
        self.set_onpeak_backup_command_tree()
        if self.state != HomeAloneState.Dormant:
            self.trigger_normal_event(HomeAloneEvent.GoDormant)
        self.HouseColdOnpeak()
        self.onpeak_backup_actuator_actions()
        self.top_state_update(cause=TopStateEvent.HouseColdOnpeak)    

    async def main(self):
        await asyncio.sleep(5)
        while not self._stop_requested:
            self._send(PatInternalWatchdogMessage(src=self.name))
            self.log(f"Top state: {self.top_state}")
            self.log(f"State: {self.state}")

            # update temperatures_available
            self.get_latest_temperatures()

            # Update top state
            if self.top_state == HomeAloneTopState.Normal:
                if self.house_is_cold_onpeak() and self.is_buffer_empty(really_empty=True) and self.is_storage_empty():
                    self.trigger_house_cold_onpeak_event()
            elif self.top_state == HomeAloneTopState.UsingBackupOnpeak and not self.is_onpeak():
                self.trigger_just_offpeak()
            elif self.top_state == HomeAloneTopState.ScadaBlind:
                if self.forecasts and self.temperatures_available:
                    self.log("Forecasts and temperatures are both available again!")
                    self.trigger_data_available()
                elif self.is_onpeak() and self.settings.oil_boiler_for_onpeak_backup:
                    if not self.scadablind_boiler:
                        self.aquastat_ctrl_switch_to_boiler(from_node=self.scada_blind_node)
                        self.scadablind_boiler = True
                        self.scadablind_scada = False
                else:
                    if not self.scadablind_scada:
                        self.aquastat_ctrl_switch_to_scada(from_node=self.scada_blind_node)
                        self.scadablind_boiler = False
                        self.scadablind_scada = True
            
            # Update state
            if self.top_state == HomeAloneTopState.Normal:
                self.engage_brain(waking_up=(self.state==HomeAloneState.Initializing))
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def engage_brain(self, waking_up: bool = False) -> None:
        """
        Manages the logic for the Normal top state, (ie. self.state)
        """
        if self.top_state != HomeAloneTopState.Normal:
            raise Exception(f"brain is only for Normal top state, not {self.top_state}")

        if waking_up:
            if self.state == HomeAloneState.Dormant:
                self.trigger_normal_event(HomeAloneEvent.WakeUp)
                self.time_since_blind = None
                self.initialized_relays = False
            if not self.initialized_relays:
                self.initialize_relays()
                self.initialized_relays = True
        
        previous_state = self.state

        if self.is_onpeak():
            self.storage_declared_ready = False
            self.full_storage_energy = None

        time_now = datetime.now(self.timezone)
        if ((time_now.hour==6 or time_now.hour==16) and time_now.minute>57) or self.zone_setpoints=={}:
            self.get_zone_setpoints()
        
        if not (self.forecasts and self.temperatures_available):
            if self.time_since_blind is None:
                self.time_since_blind = time.time()
            elif time.time() - self.time_since_blind > self.BLIND_MINUTES*60:
                self.log("Scada is missing forecasts and/or critical temperatures since at least 5 min.")
                self.log("Moving into ScadaBlind top state")
                self.trigger_missing_data()
            elif self.time_since_blind is not None:
                self.log(f"Blind since {int(time.time() - self.time_since_blind)} seconds")
        else:
            if self.time_since_blind is not None:
                self.time_since_blind = None
            if self.state==HomeAloneState.Initializing:
                if self.temperatures_available:
                    if self.is_onpeak():
                        if self.is_buffer_empty():
                            if self.is_storage_colder_than_buffer():
                                self.trigger_normal_event(HomeAloneEvent.OnPeakStorageColderThanBuffer)
                            else:
                                self.trigger_normal_event(HomeAloneEvent.OnPeakBufferEmpty)
                        else:
                            self.trigger_normal_event(HomeAloneEvent.OnPeakBufferFull)
                    else:
                        if self.is_buffer_empty():
                            self.trigger_normal_event(HomeAloneEvent.OffPeakBufferEmpty)
                        else:
                            if self.is_storage_ready():
                                self.trigger_normal_event(HomeAloneEvent.OffPeakBufferFullStorageReady)
                            else:
                                self.trigger_normal_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady)

            elif self.state==HomeAloneState.HpOnStoreOff:
                if self.is_onpeak():
                    self.trigger_normal_event(HomeAloneEvent.OnPeakStart)
                elif self.is_buffer_full():
                    if self.is_storage_ready():
                        self.trigger_normal_event(HomeAloneEvent.OffPeakBufferFullStorageReady)
                    else:
                        usable = self.data.latest_channel_values[H0N.usable_energy] / 1000
                        required = self.data.latest_channel_values[H0N.required_energy] / 1000
                        if usable < required:
                            self.trigger_normal_event(HomeAloneEvent.OffPeakBufferFullStorageNotReady)
                        else:
                            self.trigger_normal_event(HomeAloneEvent.OffPeakBufferFullStorageReady)
                
            elif self.state==HomeAloneState.HpOnStoreCharge:
                if self.is_onpeak():
                    self.trigger_normal_event(HomeAloneEvent.OnPeakStart)
                elif self.is_buffer_empty():
                    self.trigger_normal_event(HomeAloneEvent.OffPeakBufferEmpty)
                elif self.is_storage_ready():
                    self.trigger_normal_event(HomeAloneEvent.OffPeakStorageReady)
                
            elif self.state==HomeAloneState.HpOffStoreOff:
                if self.is_onpeak():
                    if self.is_buffer_empty() and not self.is_storage_colder_than_buffer():
                        self.trigger_normal_event(HomeAloneEvent.OnPeakBufferEmpty)
                else:
                    if self.is_buffer_empty():
                        self.trigger_normal_event(HomeAloneEvent.OffPeakBufferEmpty)
                    elif not self.is_storage_ready():
                        usable = self.data.latest_channel_values[H0N.usable_energy] / 1000
                        required = self.data.latest_channel_values[H0N.required_energy] / 1000
                        if self.storage_declared_ready:
                            if self.full_storage_energy is None:
                                if usable > 0.9*required:
                                    self.log("The storage was already declared ready during this off-peak period")
                                else:
                                    self.trigger_normal_event(HomeAloneEvent.OffPeakStorageNotReady)
                            else:
                                if usable > 0.9*self.full_storage_energy:
                                    self.log("The storage was already declared full during this off-peak period")
                                else:
                                    self.trigger_normal_event(HomeAloneEvent.OffPeakStorageNotReady)
                        else:
                            self.trigger_normal_event(HomeAloneEvent.OffPeakStorageNotReady)

            elif self.state==HomeAloneState.HpOffStoreDischarge:
                if not self.is_onpeak():
                    self.trigger_normal_event(HomeAloneEvent.OffPeakStart)
                elif self.is_buffer_full():
                    self.trigger_normal_event(HomeAloneEvent.OnPeakBufferFull)
                elif self.is_storage_colder_than_buffer():
                    self.trigger_normal_event(HomeAloneEvent.OnPeakStorageColderThanBuffer)

        if (self.state != previous_state) and self.top_state == HomeAloneTopState.Normal:
            self.update_relays(previous_state)


    def update_relays(self, previous_state) -> None:
        if self.top_state != HomeAloneTopState.Normal:
            raise Exception("Can not go into update_relays if top state is not Normal")
        if self.state == HomeAloneState.Dormant or self.state == HomeAloneState.Initializing:
            return
        if "HpOn" not in previous_state and "HpOn" in self.state:
            self.turn_on_HP(from_node=self.normal_node)
        if "HpOff" not in previous_state and "HpOff" in self.state:
            self.turn_off_HP(from_node=self.normal_node)
        if "StoreDischarge" in self.state:
            self.turn_on_store_pump(from_node=self.normal_node)
        else:
            self.turn_off_store_pump(from_node=self.normal_node)         
        if "StoreCharge" in self.state:
            self.valved_to_charge_store(from_node=self.normal_node)
        else:
            self.valved_to_discharge_store(from_node=self.normal_node)

    def initialize_relays(self):
        if self.top_state != HomeAloneTopState.Normal:
            raise Exception("Can not go into initialize relays if top state is not Normal")
        self.log("Initializing relays")
        my_relays =  {
            relay
            for relay in self.my_actuators()
            if relay.ActorClass == ActorClass.Relay and self.is_boss_of(relay)
        }
        for relay in my_relays - {
            self.store_charge_discharge_relay, # keep as it was
            self.hp_failsafe_relay,
            self.hp_scada_ops_relay, # keep as it was unless on peak
            self.aquastat_control_relay 
        }:
            self.de_energize(relay, from_node=self.normal_node)
        self.hp_failsafe_switch_to_scada(from_node=self.normal_node)
        self.aquastat_ctrl_switch_to_scada(from_node=self.normal_node)

        if self.is_onpeak():
            self.log("Is on peak: turning off HP")
            self.turn_off_HP(from_node=self.normal_node)
    
    def trigger_just_offpeak(self):
        """
        Called to change top state from HouseColdOnpeak to Normal
        What it does:
            - flip relays as needed
            - trigger the top state change
            - change 
        """
        # HouseColdOnpeak: Normal -> UsingBackupOnpeak
        if self.top_state != HomeAloneTopState.UsingBackupOnpeak:
            raise Exception("Should only call leave_onpeak_backup in transition from UsingBackupOnpeak to Normal!")
        self.JustOffpeak()
        # Report state change to scada
        self.top_state_update(cause=TopStateEvent.JustOffpeak)
        # implement the change in command tree. Boss: h.onpeak-backup -> h.n
        self.set_normal_command_tree()
        # and let the normal homealone know its alive 
        if self.state == HomeAloneState.Dormant:
            self.engage_brain(waking_up=True)

    def trigger_missing_data(self):
        if self.top_state != HomeAloneTopState.Normal:
            raise Exception("Should only call trigger_missing_data in transition from Normal to ScadaBlind!")
        self.set_scadablind_command_tree()
        if self.state != HomeAloneState.Dormant:
            self.trigger_normal_event(HomeAloneEvent.GoDormant)
        self.MissingData()
        self.scada_blind_actuator_actions()
        self.top_state_update(cause=TopStateEvent.MissingData)
        self.scadablind_boiler = False
        self.scadablind_scada = False

    def trigger_data_available(self):
        if self.top_state != HomeAloneTopState.ScadaBlind:
            raise Exception("Should only call trigger_data_available in transition from ScadaBlind to Normal!")
        self.DataAvailable()
        self.top_state_update(cause=TopStateEvent.DataAvailable)
        self.set_normal_command_tree()
        if self.state == HomeAloneState.Dormant:
            self.engage_brain(waking_up=True)

    def scada_blind_actuator_actions(self) -> None:
        """
        Expects self.scada_blind_node as boss.  Heats with heat pump:
          - turns off store pump
          - iso valve open (valved to discharge)
          - turn hp failsafe to aquastat
        """
        self.turn_off_store_pump(from_node=self.scada_blind_node)
        self.valved_to_discharge_store(from_node=self.scada_blind_node)
        self.hp_failsafe_switch_to_aquastat(from_node=self.scada_blind_node)
        
    def onpeak_backup_actuator_actions(self) -> None:
        """
        Expects set_onpeak_backup_command_tree already called, 
        with self.onpeak_backup_node as boss
          - turns off store pump
          - iso valve open (valved to discharge)
          - if using oil boiler, turns hp failsafe to aquastat and aquastat ctrl to boiler
          - if not using oil boiler, turns on heat pump

        """
        self.turn_off_store_pump(from_node=self.onpeak_backup_node)
        self.valved_to_discharge_store(from_node=self.onpeak_backup_node)
        if self.settings.oil_boiler_for_onpeak_backup:
            self.hp_failsafe_switch_to_aquastat(from_node=self.onpeak_backup_node)
            self.aquastat_ctrl_switch_to_boiler(from_node=self.onpeak_backup_node)
        else:
            self.turn_on_HP(from_node=self.onpeak_backup_node)

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
                if len(self.my_actuators()) > 0:
                    raise Exception("HomeAlone sent GoDormant with live actuators under it!")
                if self.top_state != HomeAloneTopState.Dormant:
                    # TopGoDormant: Normal/UsingBackupOnpeak -> Dormant
                    self.TopGoDormant()
                    self.top_state_update(cause=TopStateEvent.TopGoDormant)
                    # in Top State HouseColdOnpeak, normal state is already Dormant
                    if self.state != HomeAloneState.Dormant:
                        # Let normal home alone know it is dormant
                        self.trigger_normal_event(HomeAloneEvent.GoDormant)
            case WakeUp():
                if self.top_state == HomeAloneState.Dormant:
                    # TopWakeUp: Dormant -> Normal
                    self.TopWakeUp()
                    # Command tree should already be set. No trouble doing it again
                    self.set_normal_command_tree() 
                    # engage brain will WakeUp: Dormant -> Initializing
                    # run the appropriate relay initialization and then
                    # evaluate if it can move into a known state
                    self.engage_brain(waking_up = True)
            case HeatingForecast():
                self.log("Received heating forecast")
                self.forecasts: HeatingForecast = message.Payload
                if self.state == HomeAloneState.Initializing:
                    self.log(f"Top state: {self.top_state}")
                    self.log(f"State: {self.state}")
                    self.engage_brain()
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
            self.log("IN SIMULATION - set all temperatures to 20 degC")
            self.latest_temperatures = {}
            for channel_name in self.temperature_channel_names:
                self.latest_temperatures[channel_name] = 20 * 1000
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
        else:
            self.temperatures_available = False
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

    def is_onpeak(self) -> bool:
        time_now = datetime.now(self.timezone)
        time_in_2min = time_now + timedelta(minutes=2)
        peak_hours = [7,8,9,10,11] + [16,17,18,19]
        if (time_now.hour in peak_hours or time_in_2min.hour in peak_hours):
            # and time_now.weekday() < 5):
            return True
        else:
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
        buffer_empty_ch_temp = round(self.to_fahrenheit(self.latest_temperatures[buffer_empty_ch]/1000),1)
        if buffer_empty_ch_temp < min_buffer:
            self.log(f"Buffer empty ({buffer_empty_ch}: {buffer_empty_ch_temp} < {min_buffer} F)")
            return True
        else:
            self.log(f"Buffer not empty ({buffer_empty_ch}: {buffer_empty_ch_temp} >= {min_buffer} F)")
            return False            
    
    def is_buffer_full(self) -> bool:
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
        buffer_full_ch_temp = round(self.to_fahrenheit(self.latest_temperatures[buffer_full_ch]/1000),1)
        if buffer_full_ch_temp > max_buffer:
            self.log(f"Buffer full ({buffer_full_ch}: {buffer_full_ch_temp} > {max_buffer} F)")
            return True
        else:
            self.log(f"Buffer not full ({buffer_full_ch}: {buffer_full_ch_temp} <= {max_buffer} F)")
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
        
    def is_storage_empty(self):
        if not self.is_simulated:
            total_usable_kwh = self.data.latest_channel_values[H0N.usable_energy] / 1000
        else:
            total_usable_kwh = 0
        if total_usable_kwh < 0.2:
            self.log("Storage is empty")
            return True
        else:
            self.log("Storage is not empty")
            return False
        
    def get_zone_setpoints(self):
        if self.is_simulated:
            self.zone_setpoints = {'zone1': 70, 'zone2': 65}
            self.log(f"IN SIMULATION - fake setpoints set to {self.zone_setpoints}")
            return
        self.zone_setpoints = {}
        temps = {}
        for zone_setpoint in [x for x in self.data.latest_channel_values if 'zone' in x and 'set' in x]:
            zone_name = zone_setpoint.replace('-set','')
            self.log(f"Found zone: {zone_name}")
            if self.data.latest_channel_values[zone_setpoint] is not None:
                self.zone_setpoints[zone_name] = self.data.latest_channel_values[zone_setpoint]
            if self.data.latest_channel_values[zone_setpoint.replace('-set','-temp')] is not None:
                temps[zone_name] = self.data.latest_channel_values[zone_setpoint.replace('-set','-temp')]
        self.log(f"Found all zone setpoints: {self.zone_setpoints}")
        self.log(f"Found all zone temperatures: {temps}")
    
    def is_house_cold(self):
        for zone in self.zone_setpoints:
            setpoint = self.zone_setpoints[zone]
            if not self.is_simulated:
                if zone+'-temp' not in self.data.latest_channel_values:
                    self.log(f"Could not find latest temperature for {zone}!")
                    continue
                temperature = self.data.latest_channel_values[zone+'-temp']
            else:
                temperature = 40
            if temperature < setpoint - 1*1000:
                self.log(f"{zone} temperature is at least 1F lower than the setpoint before starting on-peak")
                return True    
        self.log("All zones are at or above their setpoint at the beginning of on-peak")
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

    def alert(self, summary: str, details: str) -> None:
        self._services._links.publish_upstream(payload=Glitch(
            FromGNodeAlias=self.layout.scada_g_node_alias,
            Node=self.normal_node,
            Type=LogLevel.Critical,
            Summary=summary,
            Details=details
        ))
        self.log(f"CRITICAL GLITCH: {summary}")

