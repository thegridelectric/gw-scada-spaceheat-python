import asyncio
import time
import uuid
from typing import List, Dict, cast
from gwproto.data_classes.data_channel import DataChannel
from data_classes.house_0_names import H0CN, H0N
from gwproto.message import Message
from gwproactor import ServicesInterface
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import RelayClosedOrOpen
from gwproto.named_types import AnalogDispatch, SingleReading, FsmFullReport
from result import Ok, Result

from actors.scada_actor import ScadaActor
from enums import LogLevel, PumpDocState, PumpDocEvent
from gwproto.data_classes.components.dfr_component import DfrComponent
from named_types import (Glitch, PumpDocTrigger, SingleMachineState)

from enum import auto

from gw.enums import GwStrEnum

class ValveControllerState(GwStrEnum):
    AllWhitewiresOff = auto()  
    WaitingForValvesToOpen = auto() 
    OnSignalToDistPump = auto()  
class PumpDoctor(ScadaActor):
    """ Responsible for detecting and fixing 010V pumps 
    """
    PUMP_POWER_THRESHOLD_W = 2
    WHITEWIRE_POWER_THRESHOLD_W = 5
    MIN_FLOW_GPM = 0.2
    PUMP_CHECK_S = 10 # seconds to wait before checking pump power
    PUMP_DEFIB_S = 5  # seconds to keep pump off
    PUMP_POWER_THRESHOLD_W = 5
    FLOW_CHECK_S = 30 # how long to wait before checking flow after pump is on
    CALEFFI_ZONE_VALVE_CONTROLLER_S = 20 # time after a whitewire that signal sent to dist pump
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.state: PumpDocState = PumpDocState.Dormant
        self.good_dist_readings = False
        self.good_primary_readings = False
        self.good_store_readings = False
        self.dist_pwr_w: int = 0
        self.dist_flow_gpm: float = 0
        self.store_pump_relay_state: RelayClosedOrOpen = RelayClosedOrOpen.RelayOpen
        self.store_pump_relay_change_s: float = 0
        self.lwt_f: float = 0
        self.whitewire_channels: List[DataChannel] = []
        self.whitewire: Dict[str, int] # ch name -> 0 / 1
        self.dist_valve_controller_state: ValveControllerState = ValveControllerState.AllWhitewiresOff
        # for i in range(len(self.layout.zone_list)):
        #     zone_idx = i+1
        #     ch_name = self.layout.channel_names.zone[zone_idx].whitewire_pwr
        #     ch = self.layout.channel(ch_name)
        #     if ch is None:
        #         raise Exception(f"What happened! Missing channel {ch_name}")
        #     self.whitewire_channels.append(ch)
        #     self.whitewire[ch.Name] = 0 # initialize with all off

    def start(self) -> None:
        ...

    def stop(self) -> None:
        """ Required method, used for stopping tasks. Noop"""
        ...

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...

    def sidelined(self) -> bool:
        """ Sidelined if it is out of the chain of command; e.g boss is own ShNode"""
        if self.boss == self.node:  # not in the command tree
            return True
        return False

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if self.sidelined():
            self.log(f"Sidelined so ignoring messages! Handle: {self.node.handle}")
            return Ok(False)
        payload = message.Payload
        
        from_node = self.layout.node(message.Header.Src, None)
        if from_node is None:
            return Ok(False)
        match payload:
            case FsmFullReport():
                ... # relays send back report when they change state
            case PumpDocTrigger():
                try:
                    self.process_pump_doc_trigger(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with process_fsm_event: {e}")
            case SingleMachineState():
                self.process_single_machine_state(from_node, payload)
            case SingleReading():
                self.process_single_reading(from_node, payload)
            case _: 
                self.log(f"{self.name} received unexpected message: {message.Header}"
                )
                return Ok(False)
        return Ok(True)

    def process_pump_doc_trigger(self, from_node: ShNode, payload: PumpDocTrigger) -> None:
        if self.boss != from_node:
            self.log(f"Ignoring trigger from {from_node.handle}. My handle is {self.node.handle}") # todo: send glitch
            return
        if payload.FromState != self.state:
            self.log(f"Ignoring trigger. payload.FromState {payload.FromState} and self.state {self.state}")
            return
        before = self.state
        if self.state == PumpDocState.Dormant:
            if payload.Trigger == PumpDocEvent.NoDistFlow:
                self.state = PumpDocState.Dist
                asyncio.create_task(self._defib_the_dist_pump())
            elif payload.Trigger == PumpDocEvent.NoStoreFlow:
                self.state = PumpDocState.Store
                asyncio.create_task(self._defib_the_store_pump())
            else:
                self.log(f"Ignoring {payload.Trigger} from state {self.state}")
        else:
            if payload.Trigger == PumpDocEvent.Timeout:
                self.state = PumpDocState.Dormant
            else:
                self.log(f"Ignoring {payload.Trigger} from state {self.state}")
        if before != self.state:
            self.log(f"{payload.Trigger}: {before} -> {self.state}")

    def process_single_machine_state(self, from_node: ShNode, sms: SingleMachineState) -> None:
        """ Detects if the store pump relay has just closed. If so, it checks the store pump """
        if from_node == self.store_pump_failsafe_relay:
            if sms.State != self.store_pump_relay_state:
                self.store_pump_relay_change_s = time.time()
                self.store_pump_relay_state = RelayClosedOrOpen(sms.State)
                if sms.State == RelayClosedOrOpen.RelayClosed:
                    asyncio.create_task(self._check_store_pump())

    def process_single_reading(self, from_node: ShNode, reading: SingleReading) -> None:
        channel = self.layout.channel(reading.ChannelName)
        if channel in self.whitewire_channels:
            if reading.Value > self.WHITEWIRE_POWER_THRESHOLD_W:
                if self.whitewire[channel.Name] == 0:
                    # this whitewire just turned on! 
                    self.whitewire[channel.Name] = 1
                    if self.dist_valve_controller_state == ValveControllerState.AllWhitewiresOff:
                        if not hasattr(self, "_dist_pump_task") or self._dist_pump_task.done():
                            self._dist_pump_task = asyncio.create_task(self._check_dist_pump())
     
            else:
                self.whitewire[channel.Name] = 0
                if not any(self.whitewire.values()):
                    self.dist_valve_controller_state = ValveControllerState.AllWhitewiresOff

    async def _check_dist_pump(self) -> None:
        """ Trigger this when the first whitewire goes on. Waits for enough time so that the 
        valve controller will have sent a signal to turn on to the distribution pump. Sends
        a NoDistFlow PumpDocTrigger if the pump isn't on and the PumpDocState is Dormant"""
        if not self.dist_valve_controller_state == ValveControllerState.AllWhitewiresOff:
            return
        if any(self.whitewire.values()):
            self.log("Waiting for valves to open")
            self.dist_valve_controller_state = ValveControllerState.WaitingForValvesToOpen
            await asyncio.sleep(self.CALEFFI_ZONE_VALVE_CONTROLLER_S)
            if self.dist_valve_controller_state == ValveControllerState.WaitingForValvesToOpen:
                self.dist_valve_controller_state = ValveControllerState.OnSignalToDistPump
                # now wait 10 seconds before checking pump power
                await asyncio.sleep(self.PUMP_CHECK_S)
                # its possible the whitewires turned off. 
                if self.dist_valve_controller_state != ValveControllerState.OnSignalToDistPump:
                    return
                # check the dist pump power
                if self.dist_pump_power_readings_exist():
                    dist_pump_pwr = self.data.latest_channel_values[H0CN.dist_pump_pwr]
                    if dist_pump_pwr < self.PUMP_POWER_THRESHOLD_W and self.state == PumpDocState.Dormant:
                        self._send_to(self.boss, PumpDocTrigger(
                            FromState=PumpDocState.Dormant,
                            ToState=PumpDocState.Dist,
                            Trigger=PumpDocEvent.NoDistFlow
                        ))
                            
    async def _check_store_pump(self) -> None:
        """ If the pump is not working and the PumpDoctors is Dormant, it sends a
        PumpDocTrigger to alert the boss.
        """
        self.log("Checking store pump")
        # Wait 10 seconds
        await asyncio.sleep(self.PUMP_CHECK_S)
        if self.store_pump_relay_state == RelayClosedOrOpen.RelayOpen:
            return
        
        # Check store pump power
        if self.store_pump_power_readings_exist():
            store_pump_pwr = self.data.latest_channel_values[H0CN.store_pump_pwr]
            if store_pump_pwr < self.PUMP_POWER_THRESHOLD_W and self.state == PumpDocState.Dormant:
                    self.log("NoStoreFlow detected!")
                    self._send_to(self.boss, PumpDocTrigger(
                        FromState=PumpDocState.Dormant,
                        ToState=PumpDocState.Store,
                        Trigger=PumpDocEvent.NoStoreFlow,
                    ))
        elif self.store_flow_readings_exist():
            # first give the flow time to show up
            await asyncio.sleep(self.FLOW_CHECK_S)
            store_flow_gpm = self.data.latest_channel_values[H0CN.store_flow] / 100
            if store_flow_gpm < self.MIN_FLOW_GPM and self.state == PumpDocState.Dormant:
                self.log("NoStoreFlow detected!")
                self._send_to(self.boss, PumpDocTrigger(
                    FromState=PumpDocState.Dormant,
                    ToState=PumpDocState.Store,
                    Trigger=PumpDocEvent.NoStoreFlow,
                ))
        else:
            self.log("store pump readings and store flow readings don't exist .. so can't check store pump")

    async def _defib_the_dist_pump(self) -> None:
        """
        Turn off heat calls for all zones and set 010V for dist pump to 0.
        Wait for TIMEOUT seconds and then send a Dormant PumpDocTrigger
        """
        # start heat calls on all white wires
        self.log("Doctoring the distribution pump")
        for zone in self.layout.zone_list:
            self.heatcall_ctrl_to_scada(zone)
            self.stat_ops_open_relay(zone)
        # caleffi zone valve controller takes about 30 seconds CHECK
        dist_010v_node = self.layout.node(H0N.dist_010v)
        # set 010V output to 0
        self._send_to(
            dist_010v_node,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=dist_010v_node.handle,
                AboutName=dist_010v_node.Name,
                Value=0,
                TriggerId=str(uuid.uuid4()),
                UnixTimeMs=int(time.time() * 1000),
            )
        )
        self.log(f"Sent analog dispatch 0 to {dist_010v_node.handle}")
        # keep pump off for 5 seconds
        await asyncio.sleep(self.PUMP_DEFIB_S)
    

        # set dist 010V output back to its default
        dfr_component = cast(DfrComponent, self.layout.node(H0N.zero_ten_out_multiplexer).component)
        dist_dfr_config = next(
                    config
                    for config in dfr_component.gt.ConfigList
                    if config.ChannelName == dist_010v_node.name
                )
        self._send_to(
            dist_010v_node,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=dist_010v_node.handle,
                AboutName=dist_010v_node.Name,
                Value=dist_dfr_config.InitialVoltsTimes100,
                TriggerId=str(uuid.uuid4()),
                UnixTimeMs=int(time.time() * 1000),
            )
        )
        self.log(f"Sent analog dispatch {dist_dfr_config.InitialVoltsTimes100}  to {dist_010v_node.handle}")
        # Send thermostat control back to the stats (and de-energize the stat_ops relays)
        for zone in self.layout.zone_list:
            self.heatcall_ctrl_to_stat(zone)
            self.stat_ops_open_relay(zone)

        # Wait again
        await asyncio.sleep(self.PUMP_DEFIB_S)

        # Check if the pump is working. Either way, report a Glitch
        try:
            dist_pump_pwr = self.data.latest_channel_values[H0CN.dist_pump_pwr]
            if dist_pump_pwr < self.PUMP_POWER_THRESHOLD_W and any(self.whitewire.values()):
                glitch = Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Critical,
                    Summary="No distribution pump activity recorded since the last heat call",
                    Details=f"dist pump power: {dist_pump_pwr}, whitewires: {self.whitewire} "
                )
            else:
                glitch = Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Info,
                    Summary="Pump doctor cycled dist pump. Looks successful",
                    Details=f"dist pump power: {dist_pump_pwr}, whitewires: {self.whitewire}"
                )
            self._send_to(self.atn, glitch)
        except Exception as e:
            self.log(f"Trouble reporting Dist Pump glitch! {e}")

        # and then exit

        self._send_to(self.boss, PumpDocTrigger(
            FromState=self.state,
            ToState=PumpDocState.Dormant,
            Trigger=PumpDocEvent.Timeout
        ))

    async def _defib_the_store_pump(self) -> None:
        """
        Set store-010V to 0,  turn off the store pump
        Wait for TIMEOUT seconds and then send a Dormant PumpDocTrigger
        """
        self.log("Doctoring the store pump")
        store_010v_node = self.layout.node(H0N.store_010v)
        # set 010V output to 0
        self._send_to(
            store_010v_node,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=store_010v_node.handle,
                AboutName=store_010v_node.Name,
                Value=0,
                TriggerId=str(uuid.uuid4()),
                UnixTimeMs=int(time.time() * 1000),
            )
        )
        self.log(f"Sent analog dispatch to {store_010v_node.handle}")
        self.turn_off_store_pump()
        await asyncio.sleep(self.PUMP_DEFIB_S)

        # set dist 010V output back to its default
        dfr_component = cast(DfrComponent, self.layout.node(H0N.zero_ten_out_multiplexer).component)
        store_dfr_config = next(
                    config
                    for config in dfr_component.gt.ConfigList
                    if config.ChannelName == store_010v_node.name
                )
        self._send_to(
            store_010v_node,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=store_010v_node.handle,
                AboutName=store_010v_node.Name,
                Value=store_dfr_config.InitialVoltsTimes100,
                TriggerId=str(uuid.uuid4()),
                UnixTimeMs=int(time.time() * 1000),
            )
        )
        self.log(f"Sent analog dispatch {store_dfr_config.InitialVoltsTimes100}  to {store_010v_node.handle}")
        # Turn store pump back on
        self.turn_on_store_pump()  

        # Wait again
        await asyncio.sleep(self.PUMP_DEFIB_S)
  
    # Check if the pump is working. Either way, report a Glitch
        try:
            store_pump_pwr = self.data.latest_channel_values[H0CN.store_pump_pwr]
            if store_pump_pwr < self.PUMP_POWER_THRESHOLD_W and self.store_pump_relay_state == RelayClosedOrOpen.RelayClosed:
                glitch = Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Critical,
                    Summary="No store pump activity since store pump relay closed",
                    Details=f"Store pump relay closed but power is {store_pump_pwr}" , 
                )
            else:
                glitch = Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.Name,
                    Type=LogLevel.Info,
                    Summary="Pump doctor cycled store pump. Looks successful",
                    Details=f"store pump power: {store_pump_pwr}, store pump: {self.store_pump_relay_state.value}"
                )
            self._send_to(self.atn, glitch)
        except Exception as e:
            self.log(f"Trouble reporting Stpre Pump glitch! {e}")
        self._send_to(self.boss, PumpDocTrigger(
            FromState=self.state,
            ToState=PumpDocState.Dormant,
            Trigger=PumpDocEvent.Timeout
        ))

    def store_pump_power_readings_exist(self) -> bool:
        if H0CN.store_pump_pwr in self.data.latest_channel_values:
            return True
        return False

    def store_flow_readings_exist(self) -> bool:
        if H0CN.store_flow in self.data.latest_channel_values:
            return True
        return False

    def dist_pump_power_readings_exist(self) -> bool:
        if H0CN.dist_pump_pwr in self.data.latest_channel_values:
            return True
        return False

    def dist_flow_readings_exist(self) -> bool:
        if H0CN.dist_flow in self.data.latest_channel_values:
            return True
        return False