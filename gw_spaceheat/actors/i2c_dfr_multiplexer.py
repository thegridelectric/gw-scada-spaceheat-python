# """Implements I2cRelayMultiplexer Actors"""
# import asyncio
# import importlib.util
# import time
# from datetime import datetime
# import smbus2
# from typing import Any, Dict, List, Optional, Sequence, cast

# from gw.enums import GwStrEnum
# # from actors.simple_sensor import SimpleSensor, SimpleSensorDriverThread
# from gwproactor import QOS, Actor, MonitoredName, ServicesInterface
# from gwproactor.message import Message, PatInternalWatchdogMessage
# from gwproto.data_classes.components.dfr_component import DfrComponent
# from gwproto.data_classes.data_channel import DataChannel
# from gwproto.data_classes.house_0_layout import House0Layout
# from gwproto.data_classes.house_0_names import H0N
# from gwproto.data_classes.sh_node import ShNode
# from gwproto.enums import ActorClass, MakeModel, TelemetryName, FsmActionType
# from gwproto.message import Header
# from gwproto.named_types import (FsmAtomicReport, FsmEvent, 
#                                  MachineStates, SingleReading,
#                                  SyncedReadings, )
# from gwproto.enums import FsmActionType
# from pydantic import BaseModel
# from result import Err, Ok, Result
# from gw.enums import GwStrEnum

# DFR_OUTPUT_SET_RANGE = 0x01
# DFR_OUTPUT_RANGE_10V = 17


# SLEEP_STEP_SECONDS = 0.1


# class I2cDfrMultiplexer(Actor):
#     LOOP_S = 300
#     node: ShNode
#     component: DfrComponent
#     event_enum: GwStrEnum
#     layout: House0Layout
#     _stop_requested: bool
#     is_simulated: bool
#     i2c_bus: Optional[Any]  # smbus2.bus()
#     dfr_val: Dict[int, int] # voltage x 100 by OutputIdx
#     my_dfrs: List[ShNode]

#     def __init__(
#         self,
#         name: str,
#         services: ServicesInterface,
#     ):
#         self.layout = cast(House0Layout, services.hardware_layout)
#         super().__init__(name, services)
#         self.component = cast(DfrComponent, self.node.component)
#         if self.component.cac.MakeModel == MakeModel.DFROBOT__DFR0971_TIMES2:
#             if self.component.gt.I2cAddressList != [94, 95]:
#                 raise Exception("Expect i2c addresses 0x5e, 0x5f for dfr 010V")
#         else:
#             raise Exception(
#                 f"Expected {MakeModel.DFROBOT__DFR0971_TIMES2}, got {self.component.cac}"
#             )
        
#         # Make/model specific
#         # Move into driver code if/when we get a second make/model
#         self.first_i2c_addr = self.component.gt.I2cAddressList[0]
#         self.second_i2c_addr = self.component.gt.I2cAddressList[1]
#         self.i2c_bus = None

#         dfr_nodes = [node for node in self.layout.nodes.values() if node.ActorClass == ActorClass.ZeroTenOutputer]
#         dfr_node_names = [config.ChannelName for config in self.component.gt.ConfigList]
#         if {node.name for node in dfr_nodes} != set(dfr_node_names):
#             raise Exception("Mismatch between config channel names and dfr actors!")
#         self.my_dfrs: List[ShNode] = dfr_nodes
#         self.dfr_val = {}
#         # dict of current energization state
#         self._stop_requested = False

#     @property
#     def primary_scada(self) -> ShNode:
#         return self.layout.nodes[H0N.primary_scada]

#     def initialize_board(self) -> None:
#         for module_name in ["smbus2"]:
#             found = importlib.util.find_spec(module_name)
#             if found is None:
#                 self.is_simulated = True
#                 break
#             self.is_simulated = False
        
#         if not self.is_simulated:
#             self.bus = smbus2.SMBus(1)
#             self.initialize_range()

#         for dfr in self.my_dfrs:
#             dfr_config = next(
#                     config
#                     for config in self.component.gt.ConfigList
#                     if config.ChannelName == dfr.name
#                 )
#             idx = dfr_config.OutputIdx
#             init = dfr_config.InitialVoltsTimes100
#             self.dfr_val[idx] = init
#             self.log(f"Setting {dfr.name} to init")

#     def initialize_range(self) -> None:
#         try:
#             self.bus.read_byte(self.first_i2c_addr)
#             self.bus.write_word_data(self.first_i2c_addr, DFR_OUTPUT_SET_RANGE, DFR_OUTPUT_RANGE_10V)
#         except Exception:
#             raise Exception(f"Failed to find DFR at addr {self.first_i2c_addr}")
#         try:
#             self.bus.read_byte(self.second_i2c_addr)
#             self.bus.write_word_data(self.second_i2c_addr, DFR_OUTPUT_SET_RANGE, DFR_OUTPUT_RANGE_10V)
#         except Exception:
#             print("No second dfr")
#             #raise Exception(f"Failed to find DFR at addr {self.second_i2c_addr}")

#     def _send_to(self, dst: ShNode, payload):
#         if dst.name in set(self.services._communicators.keys()) | {self.services.name}:
#             self._send(
#                 Message(
#                     header=Header(
#                         Src=self.name,
#                         Dst=dst.name,
#                         MessageType=payload.TypeName,
#                     ),
#                     Payload=payload,
#                 )
#             )
#         else:
#             # Otherwise send via local mqtt
#             message = Message(Src=self.name, Dst=dst.name, Payload=payload)
#             return self.services._links.publish_message(
#                 self.services.LOCAL_MQTT, message, qos=QOS.AtMostOnce
#             )

#     def get_idx(self, dfr: ShNode) -> Optional[int]:
#         if not dfr.actor_class == ActorClass.ZeroTenOutputer:
#             return None
#         dfr_config = next(
#             (
#                 config
#                 for config in self.component.gt.ConfigList
#                 if config.ChannelName == dfr.name
#             ),
#             None,
#         )
#         if dfr_config is None:
#             return None
#         return dfr_config.OutputIdx

#     def get_channel(self, relay: ShNode) -> Optional[DataChannel]:
#         if not relay.actor_class == ActorClass.Relay:
#             return None
#         relay_config = next(
#             (
#                 config
#                 for config in self.component.gt.ConfigList
#                 if config.ActorName == relay.name
#             ),
#             None,
#         )
#         if relay_config is None:
#             raise Exception(f"relay {relay} does not have a state channel!")
#         return self.layout.data_channels[relay_config.ChannelName]

#     def _dispatch_dfr(self, dispatch: FsmEvent) -> Result[bool, BaseException]:
#         if dispatch.EventType != ChangeRelayPin.enum_name():
#             return
#         relay = self.layout.node_by_handle(dispatch.FromHandle)
#         if relay is None:
#             return Err(
#                 ValueError(f"message.FromHandle {dispatch.FromHandle} not in layout!")
#             )
#         ChangeRelayPin.Energize
#         idx = self.get_idx(relay)
#         if idx is None:
#             return Err(ValueError(f"Not a valid relay: {relay}"))

#         try:
#             if dispatch.EventName == ChangeRelayPin.Energize.value:
#                 self.krida_relay_pin[idx].value = ChangeKridaPin.Energize.value
#                 self.relay_state[idx] = RelayEnergizationState.Energized
#             else:
#                 self.krida_relay_pin[idx].value = ChangeKridaPin.DeEnergize.value
#                 self.relay_state[idx] = RelayEnergizationState.DeEnergized
#         except Exception as e:
#             return Err(ValueError(f"Trouble setting relay {idx} via i2c: {e}"))
#         channel = self.get_channel(relay)
#         if channel.TelemetryName != TelemetryName.RelayState:
#             raise Exception(
#                 "relay state channels should have telemetry name RelayState"
#             )
#         t_ms = int(time.time() * 1000)
#         self._send_to(
#             self.primary_scada,
#             SingleReading(
#                 ChannelName=channel.Name,
#                 Value=self.relay_state[idx].value,
#                 ScadaReadTimeUnixMs=t_ms,
#             ),
#         )
#         self._send_to(
#             relay,
#             FsmAtomicReport(
#                 MachineHandle=self.node.handle,
#                 StateEnum="relay.pin",
#                 ReportType=FsmReportType.Action,
#                 ActionType=FsmActionType.RelayPinSet,
#                 Action=self.relay_state[idx].value,
#                 UnixTimeMs=t_ms,
#                 TriggerId=dispatch.TriggerId,
#             ),
#         )
#         return Ok()

#     def _process_event_message(self, message: FsmEvent) -> Result[bool, BaseException]:
#         if message.ToHandle != self.node.handle:
#             print(f"Not a message for {self.node.Handle}: {message}")
#             return
#         if message.EventType != ChangeRelayPin.enum_name():
#             print(f"Not a ChangeRelayPin event type. Ignoring: {message}")
#             return
#         if message.EventName not in ChangeRelayPin.values():
#             print(
#                 f"EventName {message.EventName} not in ChangeRelayPin values {ChangeRelayPin.values()}"
#             )
#             return
#         self._dispatch_relay_pin(message)
#         return Ok()

#     def process_message(self, message: Message) -> Result[bool, BaseException]:
#         if isinstance(message.Payload, FsmEvent):
#             return self._process_event_message(message.Payload)
#         return Err(
#             ValueError(
#                 f"Error. Relay {self.name} receieved unexpected message: {message.Header}"
#             )
#         )

#     @property
#     def monitored_names(self) -> Sequence[MonitoredName]:
#         return [MonitoredName(self.name, self.LOOP_S * 2)]

#     async def maintain_relay_states(self):
#         while not self._stop_requested:
#             self._send(PatInternalWatchdogMessage(src=self.name))
#             await asyncio.sleep(self.LOOP_S)
#             channel_names = []
#             values = []
#             ft = datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")
#             for relay in self.my_relays:
#                 idx = self.get_idx(relay)
#                 channel_names.append(self.get_channel(relay).Name)
#                 if self.relay_state[idx] == RelayEnergizationState.Energized:
#                     self.krida_relay_pin[idx].value = KridaPinState.Energized.value
#                     values.append(RelayEnergizationState.Energized.value)
#                     print(f"[{ft}] {relay.name}: Make sure Energized")
#                 else:
#                     self.krida_relay_pin[idx].value = KridaPinState.DeEnergized.value
#                     values.append(RelayEnergizationState.DeEnergized.value)
#                     print(f"[{ft}] {relay.name}: Make sure DeEnergized")
#             readings = SyncedReadings(
#                 ChannelNameList=channel_names,
#                 ValueList=values,
#                 ScadaReadTimeUnixMs=int(time.time() * 1000),
#             )
#             print(f"sending these readings to primary scada: {readings}")
#             self._send_to(self.primary_scada, readings)

#     def start(self) -> None:
#         self.initialize_board()
#         self.services.add_task(
#             asyncio.create_task(
#                 self.maintain_relay_states(), name="maintain_relay_states"
#             )
#         )

#     def stop(self) -> None:
#         """
#         IOLoop will take care of shutting down webserver interaction.
#         Here we stop periodic reporting task.
#         """
#         self._stop_requested = True

#     async def join(self) -> None:
#         """IOLoop will take care of shutting down the associated task."""

#     def log(self, note: str) -> None:
#         log_str = f"[{self.name}] {note}"
#         self.services.logger.error(log_str)


# def krida_to_gw(krida_board: int, krida_idx: int) -> int:
#     if krida_idx < 9:
#         return krida_board * 16 + (9 - krida_idx)
#     else:
#         return krida_board * 16 + krida_idx


# def gw_to_board_idx(gw_idx: int) -> int:
#     return int((gw_idx - 1) / 16)


# def board_from_gw_idx(gw_idx: int) -> int:
#     return int((gw_idx - 1) / 16) + 1


# def gw_to_pin(gw_idx: int) -> int:
#     i = (gw_idx - 1) % 16 + 1
#     krida_idx = 0
#     if i < 9:
#         krida_idx = 9 - i
#     else:
#         krida_idx = i
#     return krida_idx - 1



