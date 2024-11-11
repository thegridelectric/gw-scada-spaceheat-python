"""Implements I2cRelayMultiplexer Actors"""
import asyncio
import importlib.util
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, cast

from gw.enums import GwStrEnum
# from actors.simple_sensor import SimpleSensor, SimpleSensorDriverThread
from gwproactor import QOS, Actor, MonitoredName, ServicesInterface
from gwproactor.message import Message, PatInternalWatchdogMessage
from gwproto.data_classes.components.i2c_multichannel_dt_relay_component import \
    I2cMultichannelDtRelayComponent
from gwproto.data_classes.data_channel import DataChannel
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (ActorClass, ChangeRelayPin, FsmActionType,
                           FsmReportType, MakeModel,
                           RelayEnergizationState, RelayWiringConfig,
                           TelemetryName)
from gwproto.message import Header
from gwproto.named_types import (FsmEvent, SingleReading,
                                 SyncedReadings, FsmAtomicReport)
from pydantic import BaseModel, Field
from result import Err, Ok, Result


class ChangeKridaPin(Enum):
    Energize = 0
    DeEnergize = 1


class KridaPinState(Enum):
    Energized = 0
    DeEnergized = 1


class SimulatedPin(BaseModel):
    value: int = Field(ge=0, le=1)


SLEEP_STEP_SECONDS = 0.1


class I2cRelayMultiplexer(Actor):
    RELAY_LOOP_S = 300
    node: ShNode
    component: I2cMultichannelDtRelayComponent
    wiring_config: RelayWiringConfig
    event_enum: GwStrEnum
    layout: House0Layout
    _stop_requested: bool
    is_simulated: bool
    i2c_bus: Optional[Any]  # board.I2C()
    krida_board: Dict[int, Any]
    relay_state: Dict[int, Any]
    my_relays: List[ShNode]

    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        self.layout = cast(House0Layout, services.hardware_layout)
        super().__init__(name, services)
        self.component = cast(I2cMultichannelDtRelayComponent, self.node.component)
        if self.component.cac.MakeModel != MakeModel.KRIDA__DOUBLEEMR16I2CV3:
            raise Exception(
                f"Expected {MakeModel.KRIDA__DOUBLEEMR16I2CV3}, got {self.component.cac}"
            )
        # Move into driver code if/when we get a second i2c relay component
        self.i2c_bus = None

        # krida_board[0] is the first krida board (# adafruit_pcf8575.PCF8575)
        # krida_board[1] is the second krida board
        self.krida_board: Dict[int, Any] = {}

        # A dict that controls the 32 pins
        self.krida_relay_pin: Dict[int, Any] = {}
        relay_node_names = [config.ActorName for config in self.component.gt.ConfigList]
        self.my_relays = [self.layout.nodes[name] for name in relay_node_names]
        self.channel_by_relay: Dict[ShNode, DataChannel] = {}
        # dict of current energization state
        self.relay_state: Dict[int, RelayEnergizationState] = {}
        self._stop_requested = False
        self.initialize_board()

    @property
    def primary_scada(self) -> ShNode:
        return self.layout.nodes[H0N.primary_scada]

    def initialize_board(self) -> None:
        for module_name in ["adafruit_pcf8575", "board"]:
            found = importlib.util.find_spec(module_name)
            if found is None:
                self.is_simulated = True
                break
            self.is_simulated = False

        if self.is_simulated:
            for relay in self.my_relays:
                idx = self.get_idx(relay)
                self.relay_state[idx] = RelayEnergizationState.DeEnergized
                self.krida_relay_pin[idx] = SimulatedPin(
                    value=KridaPinState.DeEnergized.value
                )
        else:
            # from starter-scripts/krida.py
            import adafruit_pcf8575
            import board

            self.i2c_bus = board.I2C()
            addresses = self.component.gt.I2cAddressList

            num_boards = 2
            for i in range(num_boards):
                board_idx = i + 1
                address = addresses[i]
                try:
                    self.krida_board[board_idx] = adafruit_pcf8575.PCF8575(
                        i2c_bus=self.i2c_bus, address=address
                    )
                except Exception as e:
                    if board_idx == 1:
                        raise Exception(
                            f"Failed to get board at {address} for board {i}: {e}"
                        ) from e
                    else:
                        print("No board 2!!")
                        continue
                time.sleep(0.2)
                print(f"initializing board at {hex(address)}")
                for j in range(1, 17):
                    # set relay to correct pin, and switch to output. This energizes all relays
                    gw_idx = (board_idx - 1) * 16 + j
                    pin_idx = gw_to_pin(gw_idx)
                    self.krida_relay_pin[gw_idx] = self.krida_board[board_idx].get_pin(
                        pin_idx
                    )
                    self.krida_relay_pin[gw_idx].switch_to_output()
                time.sleep(1)
                for j in range(1, 17):
                    # move all relays back to de-energized position
                    self.krida_relay_pin[
                        i * 16 + j
                    ].value = ChangeKridaPin.DeEnergize.value
                # and record the de-energized state for all known relays
                print(f"Done initializing board {board_idx}")
                for relay in self.my_relays:
                    self.relay_state[
                        self.get_idx(relay)
                    ] = RelayEnergizationState.DeEnergized

    def _send_to(self, dst: ShNode, payload):
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

    def get_idx(self, relay: ShNode) -> Optional[int]:
        if not relay.actor_class == ActorClass.Relay:
            return None
        relay_config = next(
            (
                config
                for config in self.component.gt.ConfigList
                if config.ActorName == relay.name
            ),
            None,
        )
        if relay_config is None:
            return None
        return relay_config.RelayIdx

    def get_channel(self, relay: ShNode) -> Optional[DataChannel]:
        if not relay.actor_class == ActorClass.Relay:
            return None
        relay_config = next(
            (
                config
                for config in self.component.gt.ConfigList
                if config.ActorName == relay.name
            ),
            None,
        )
        if relay_config is None:
            raise Exception(f"relay {relay} does not have a state channel!")
        return self.layout.data_channels[relay_config.ChannelName]

    def _dispatch_relay_pin(self, dispatch: FsmEvent) -> Result[bool, BaseException]:
        if dispatch.EventType != ChangeRelayPin.enum_name():
            return
        relay = self.layout.node_by_handle(dispatch.FromHandle)
        if relay is None:
            return Err(
                ValueError(f"message.FromHandle {dispatch.FromHandle} not in layout!")
            )
        ChangeRelayPin.Energize
        idx = self.get_idx(relay)
        if idx is None:
            return Err(ValueError(f"Not a valid relay: {relay}"))

        try:
            if dispatch.EventName == ChangeRelayPin.Energize.value:
                self.krida_relay_pin[idx].value = ChangeKridaPin.Energize.value
                self.relay_state[idx] = RelayEnergizationState.Energized
            else:
                self.krida_relay_pin[idx].value = ChangeKridaPin.DeEnergize.value
                self.relay_state[idx] = RelayEnergizationState.DeEnergized
        except Exception as e:
            return Err(ValueError(f"Trouble setting relay {idx} via i2c: {e}"))
        channel = self.get_channel(relay)
        if channel.TelemetryName != TelemetryName.RelayState:
            raise Exception(
                "relay state channels should have telemetry name RelayState"
            )
        t_ms = int(time.time() * 1000)
        self._send_to(
            self.primary_scada,
            SingleReading(
                ChannelName=channel.Name,
                Value=self.relay_state[idx].value,
                ScadaReadTimeUnixMs=t_ms,
            ),
        )
        self._send_to(
            relay,
            FsmAtomicReport(
                MachineHandle=self.node.handle,
                StateEnum="relay.pin",
                ReportType=FsmReportType.Action,
                ActionType=FsmActionType.RelayPinSet,
                Action=self.relay_state[idx].value,
                UnixTimeMs=t_ms,
                TriggerId=dispatch.TriggerId,
            ),
        )
        return Ok()

    def _process_event_message(self, message: FsmEvent) -> Result[bool, BaseException]:
        if message.ToHandle != self.node.handle:
            print(f"Not a message for {self.node.Handle}: {message}")
            return
        if message.EventType != ChangeRelayPin.enum_name():
            print(f"Not a ChangeRelayPin event type. Ignoring: {message}")
            return
        if message.EventName not in ChangeRelayPin.values():
            print(
                f"EventName {message.EventName} not in ChangeRelayPin values {ChangeRelayPin.values()}"
            )
            return
        self._dispatch_relay_pin(message)
        return Ok()

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, FsmEvent):
            return self._process_event_message(message.Payload)
        return Err(
            ValueError(
                f"Error. Relay {self.name} receieved unexpected message: {message.Header}"
            )
        )

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.RELAY_LOOP_S * 2)]

    async def maintain_relay_states(self):
        while not self._stop_requested:
            self._send(PatInternalWatchdogMessage(src=self.name))
            await asyncio.sleep(self.RELAY_LOOP_S)
            channel_names = []
            values = []
            ft = datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")
            for relay in self.my_relays:
                idx = self.get_idx(relay)
                channel_names.append(self.get_channel(relay).Name)
                if self.relay_state[idx] == RelayEnergizationState.Energized:
                    self.krida_relay_pin[idx].value = KridaPinState.Energized.value
                    values.append(RelayEnergizationState.Energized.value)
                    print(f"[{ft}] {relay.name}: Make sure Energized")
                else:
                    self.krida_relay_pin[idx].value = KridaPinState.DeEnergized.value
                    values.append(RelayEnergizationState.DeEnergized.value)
                    print(f"[{ft}] {relay.name}: Make sure DeEnergized")
            readings = SyncedReadings(
                ChannelNameList=channel_names,
                ValueList=values,
                ScadaReadTimeUnixMs=int(time.time() * 1000),
            )
            print(f"sending these readings to primary scada: {readings}")
            self._send_to(self.primary_scada, readings)

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(
                self.maintain_relay_states(), name="maintain_relay_states"
            )
        )

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""


def krida_to_gw(krida_board: int, krida_idx: int) -> int:
    if krida_idx < 9:
        return krida_board * 16 + (9 - krida_idx)
    else:
        return krida_board * 16 + krida_idx


def gw_to_board_idx(gw_idx: int) -> int:
    return int((gw_idx - 1) / 16)


def board_from_gw_idx(gw_idx: int) -> int:
    return int((gw_idx - 1) / 16) + 1


def gw_to_pin(gw_idx: int) -> int:
    i = (gw_idx - 1) % 16 + 1
    krida_idx = 0
    if i < 9:
        krida_idx = 9 - i
    else:
        krida_idx = i
    return krida_idx - 1
