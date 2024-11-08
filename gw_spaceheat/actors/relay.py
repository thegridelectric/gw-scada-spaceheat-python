"""Implements Relay Actors"""
import time
from typing import Dict, List, cast

from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface
from gwproactor.message import Message
from gwproto.data_classes.components.i2c_multichannel_dt_relay_component import \
    I2cMultichannelDtRelayComponent
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (ChangeRelayPin, FsmEventType, FsmName,
                           FsmReportType, MakeModel, RelayClosedOrOpen,
                           RelayWiringConfig, StoreFlowDirection)
from gwproto.enums.relay_event_base import RelayEventBase
from gwproto.message import Header
from gwproto.named_types import (FsmAtomicReport, FsmEvent, FsmFullReport,
                                 SingleReading)
from gwproto.type_helpers import EVENT_ENUM_BY_NAME
from result import Err, Ok, Result


class Relay(Actor):
    node: ShNode
    component: I2cMultichannelDtRelayComponent
    wiring_config: RelayWiringConfig
    my_event: GwStrEnum
    reports_by_trigger: Dict[str, List[FsmAtomicReport]]
    boss_by_trigger: Dict[str, ShNode]
    my_event: RelayEventBase
    energized_state: str
    de_energized_state: str

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
        self.relay_actor_config = next(
            (x for x in self.component.gt.ConfigList if x.ActorName == self.node.name),
            None,
        )

        if self.relay_actor_config is None:
            raise Exception(
                f"Relay {self.node.name} not in component {self.component}'s RelayActorConfigList:\n"
                f"{self.component.gt.ConfigList}"
            )

        self.relay_idx = self.relay_actor_config.RelayIdx
        self.my_event = EVENT_ENUM_BY_NAME[self.relay_actor_config.EventType]
        self.de_energizing_event = self.relay_actor_config.DeEnergizingEvent
        self.reports_by_trigger = {}
        self.boss_by_trigger = {}
        self.initialize_fsm_states()

    def initialize_fsm_states(self):
        if self.name in {H0N.vdc_relay, H0N.tstat_common_relay}:
            self.de_energized_state = RelayClosedOrOpen.RelayClosed
            self.energized_state = RelayClosedOrOpen.RelayOpen
        elif self.name == H0N.store_charge_discharge_relay:
            # TODO: there are actually 4 obvious states, since the
            # relays take 140 seconds to change position
            self.de_energized_state = StoreFlowDirection.ValvedtoDischargeStore
            self.energized_state = StoreFlowDirection.ValvedtoChargeStore
        else:
            raise Exception(f"Unknown relay {self.name}!")
        self.state = self.de_energized_state

    @property
    def fsm_name(self) -> str:
        if self.name == H0N.vdc_relay:
            return FsmName.RelayState
        elif self.name == H0N.tstat_common_relay:
            return FsmName.RelayState
        elif self.name == H0N.store_charge_discharge_relay:
            return FsmName.StoreFlowDirection
        else:
            raise Exception("Need to add!")

    @property
    def relay_multiplexer(self) -> ShNode:
        return self.layout.node(H0N.relay_multiplexer)

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

    def _process_event_message(
        self, from_name: str, message: FsmEvent
    ) -> Result[bool, BaseException]:
        self.message = message
        from_node = self.layout.node(from_name)
        if message.FromHandle != from_node.handle:
            print(
                f"from_node {from_node.name} has handle {from_node.handle}, not {message.FromHandle}!"
            )
            return

        if message.ToHandle != self.node.Handle:
            # TODO: turn this into a report?
            print(f"Handle is {self.node.Handle}; ignoring {message}")
            return

        if EVENT_ENUM_BY_NAME[message.EventType] != self.my_event:
            print(f"Not a {self.my_event} event type. Ignoring: {message}")

        # consider replacing below with actual finite state machine
        changing_state = False
        if message.EventName == self.de_energizing_event:
            relay_pin_event = ChangeRelayPin.DeEnergize
            if self.state is self.energized_state:
                changing_state = True
                new_state = self.de_energized_state
                old_pin_state = "Energized"
                new_pin_state = "DeEnergized"
        else:
            relay_pin_event = ChangeRelayPin.Energize
            if self.state is self.de_energized_state:
                changing_state = True
                new_state = self.energized_state
                old_pin_state = "DeEnergized"
                new_pin_state = "Energized"

        if changing_state:
            report = FsmAtomicReport(
                FromHandle=message.FromHandle,
                AboutFsm=self.fsm_name,
                ReportType=FsmReportType.Event,
                EventType=self.my_event,
                Event=message.EventName,
                FromState=self.state,
                ToState=new_state,
                UnixTimeMs=message.SendTimeUnixMs,
                TriggerId=message.TriggerId,
            )
            self.reports_by_trigger[message.TriggerId] = [report]
            self.boss_by_trigger[message.TriggerId] = from_node

            self.state = new_state
            print(f"sending {relay_pin_event} to multiplexer")
            #  To actually create an action, send to relay multiplexer
            pin_change_event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.relay_multiplexer.handle,
                EventType=FsmEventType.ChangeRelayPin,
                EventName=relay_pin_event,
                TriggerId=message.TriggerId,
                SendTimeUnixMs=int(time.time() * 1000),
            )
            self._send_to(self.relay_multiplexer, pin_change_event)

            self.reports_by_trigger[message.TriggerId].append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    AboutFsm=FsmName.RelayPinState,
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.ChangeRelayPin,
                    Event=relay_pin_event,
                    FromState=old_pin_state,
                    ToState=new_pin_state,
                    UnixTimeMs=pin_change_event.SendTimeUnixMs,
                    TriggerId=message.TriggerId,
                )
            )
            return Ok()

    def _process_atomic_report(
        self, message: FsmAtomicReport
    ) -> Result[bool, BaseException]:
        if message.TriggerId not in self.reports_by_trigger:
            raise Exception("Unknown trigger!!")
        self.reports_by_trigger[message.TriggerId].append(message)
        boss = self.boss_by_trigger[message.TriggerId]
        # print(f"Sending report to {boss.name}")
        self._send_to(
            boss,
            FsmFullReport(
                FromName=self.name,
                TriggerId=message.TriggerId,
                AtomicList=self.reports_by_trigger[message.TriggerId],
            ),
        )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, FsmEvent):
            return self._process_event_message(
                from_name=message.Header.Src, message=message.Payload
            )
        elif (
            isinstance(message.Payload, FsmAtomicReport)
            and message.Header.Src == self.relay_multiplexer.name
        ):
            return self._process_atomic_report(message.Payload)

        return Err(
            ValueError(
                f"Error. Relay {self.name} receieved unexpected message: {message.Header}"
            )
        )

    def start(self) -> None:
        ...

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        ...

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...
