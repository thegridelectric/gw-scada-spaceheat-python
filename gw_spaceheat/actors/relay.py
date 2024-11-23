"""Implements Relay Actors"""
import asyncio
import time
from typing import Dict, List, cast, Sequence, Optional

from gw.enums import GwStrEnum
from gwproto.data_classes.data_channel import DataChannel
from gwproactor import QOS, Actor, ServicesInterface, MonitoredName
from gwproactor.message import Message, PatInternalWatchdogMessage
from gwproto.data_classes.components.i2c_multichannel_dt_relay_component import (
    I2cMultichannelDtRelayComponent,
)
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (
    AquastatControl,
    ChangeAquastatControl,
    ChangeHeatPumpControl,
    ChangePrimaryPumpControl,
    ChangeRelayPin,
    ChangeRelayState,
    ChangeStoreFlowRelay,
    FsmReportType,
    HeatPumpControl,
    MakeModel,
    PrimaryPumpControl,
    RelayClosedOrOpen,
    RelayWiringConfig,
    StoreFlowRelay,
)
from gwproto.message import Header
from gwproto.named_types import FsmAtomicReport, FsmEvent, FsmFullReport, MachineStates
from result import Err, Ok, Result
from transitions import Machine


class Relay(Actor):
    STATE_REPORT_S = 300
    node: ShNode
    component: I2cMultichannelDtRelayComponent
    wiring_config: RelayWiringConfig
    my_state_enum: GwStrEnum
    my_event_enum: GwStrEnum
    reports_by_trigger: Dict[str, List[FsmAtomicReport]]
    boss_by_trigger: Dict[str, ShNode]
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

        self.de_energizing_event = self.relay_actor_config.DeEnergizingEvent
        self.primary_scada = self.layout.node(H0N.primary_scada)
        self.relay_multiplexer = self.layout.node(H0N.relay_multiplexer)
        self.reports_by_trigger = {}
        self.boss_by_trigger = {}
        self.my_event_enum = ChangeRelayState.enum_name()
        self.my_state_enum = RelayClosedOrOpen.enum_name()
        self.initialize_fsm()
        self._stop_requested = False

    def my_channel(self) -> DataChannel:
        relay_config = next(
            (
                config
                for config in self.component.gt.ConfigList
                if config.ActorName == self.name
            ),
            None,
        )
        if relay_config is None:
            raise Exception(f"relay {self.name} does not have a state channel!")
        return self.layout.data_channels[relay_config.ChannelName]

    def _send_to(self, dst: ShNode, payload) -> None:
        if dst is None:
            return
        message = Message(Src=self.name, Dst=dst.name, Payload=payload)
        if dst.name in set(self.services._communicators.keys()) | {self.services.name}:
            self.services.send(message)
        elif dst.Name == H0N.admin:
            self.services._links.publish_message(self.services.ADMIN_MQTT, message)
        elif dst.Name == H0N.atn:
            self.services._links.publish_upstream(payload)
        else:
            self.services._links.publish_message(self.services.LOCAL_MQTT, message)

    def _process_event_message(
        self, from_name: str, message: FsmEvent
    ) -> Result[bool, BaseException]:
        from_node = self.layout.node(from_name)
        if from_node is None:
            return
        if message.FromHandle != from_node.handle:
            self.log(
                f"from_node {from_node.name} has handle {from_node.handle}, not {message.FromHandle}!"
            )
            return

        if message.ToHandle != self.node.Handle:
            # TODO: turn this into a report?
            print(f"Handle is {self.node.Handle}; ignoring {message}")
            return

        if message.EventType != self.my_event_enum.enum_name():
            print(f"Not a {self.my_event_enum} event type. Ignoring: {message}")

        orig_state = self.state
        self.trigger(message.EventName)
        if self.state == orig_state:
            print(f"{message.EventName} did not change state {self.state}")
        else:
            # state changed
            if message.EventName == self.de_energizing_event:
                relay_pin_event = ChangeRelayPin.DeEnergize
                old_pin_state = "Energized"
                new_pin_state = "DeEnergized"
            else:
                relay_pin_event = ChangeRelayPin.Energize
                old_pin_state = "DeEnergized"
                new_pin_state = "Energized"

            report = FsmAtomicReport(
                MachineHandle=self.node.handle,
                StateEnum=self.my_state_enum.enum_name(),
                ReportType=FsmReportType.Event,
                EventEnum=self.my_event_enum.enum_name(),
                Event=message.EventName,
                FromState=orig_state,
                ToState=self.state,
                UnixTimeMs=message.SendTimeUnixMs,
                TriggerId=message.TriggerId,
            )
            self.reports_by_trigger[message.TriggerId] = [report]
            self.boss_by_trigger[message.TriggerId] = from_node
            now_ms = int(time.time() * 1000)
            # self.services.logger.warning(f"sending {relay_pin_event} to multiplexer")
            #  To actually create an action, send to relay multiplexer
            pin_change_event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.relay_multiplexer.handle,
                EventType=ChangeRelayPin.enum_name(),
                EventName=relay_pin_event,
                TriggerId=message.TriggerId,
                SendTimeUnixMs=now_ms,
            )
            self._send_to(self.relay_multiplexer, pin_change_event)
            self.send_state(now_ms)
            self.reports_by_trigger[message.TriggerId].append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum="relay.pin",
                    ReportType=FsmReportType.Event,
                    EventType=ChangeRelayPin.enum_name(),
                    Event=relay_pin_event,
                    FromState=old_pin_state,
                    ToState=new_pin_state,
                    UnixTimeMs=now_ms,
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

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.STATE_REPORT_S * 2.1)]

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="relay state reporter")
        )

    async def main(self) -> None:
        await asyncio.sleep(2)
        self.send_state()

        while not self._stop_requested:
            hiccup = 1.2
            sleep_s = max(
                hiccup, self.STATE_REPORT_S - (time.time() % self.STATE_REPORT_S) - 2
            )
            await asyncio.sleep(sleep_s)
            if sleep_s != hiccup:
                self.send_state()
                self._send(PatInternalWatchdogMessage(src=self.name))

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...

    def send_state(self, now_ms: Optional[int] = None) -> None:
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        self.services.logger.error(f"[{self.my_channel().Name}] {self.state}")
        self._send_to(
            self.primary_scada,
            MachineStates(
                MachineHandle=self.node.handle,
                StateEnum=self.my_state_enum.enum_name(),
                StateList=[self.state],
                UnixMsList=[now_ms],
            ),
        )

    def initialize_fsm(self):
        if self.name in {
            H0N.vdc_relay,
            H0N.tstat_common_relay,
            H0N.hp_scada_ops_relay,
            H0N.store_pump_failsafe,
            H0N.primary_pump_scada_ops,
        }:
            self.my_state_enum = RelayClosedOrOpen
            self.my_event_enum = ChangeRelayState
            self.transitions = [
                {
                    "trigger": ChangeRelayState.CloseRelay,
                    "source": RelayClosedOrOpen.RelayOpen,
                    "dest": RelayClosedOrOpen.RelayClosed,
                },
                {
                    "trigger": ChangeRelayState.CloseRelay,
                    "source": RelayClosedOrOpen.RelayClosed,
                    "dest": RelayClosedOrOpen.RelayClosed,
                },
                {
                    "trigger": ChangeRelayState.OpenRelay,
                    "source": RelayClosedOrOpen.RelayClosed,
                    "dest": RelayClosedOrOpen.RelayOpen,
                },
                {
                    "trigger": ChangeRelayState.OpenRelay,
                    "source": RelayClosedOrOpen.RelayOpen,
                    "dest": RelayClosedOrOpen.RelayOpen,
                },
            ]
            if self.name in {
                H0N.vdc_relay,
                H0N.tstat_common_relay,
                H0N.hp_scada_ops_relay,
            }:
                if self.de_energizing_event != ChangeRelayState.CloseRelay:
                    raise Exception(
                        f"Expect CloseRelay as de-energizing event for {self.name}; got {self.de_energizing_event}"
                    )
                self.de_energized_state = RelayClosedOrOpen.RelayClosed
                self.energized_state = RelayClosedOrOpen.RelayOpen
            else:
                if self.de_energizing_event != ChangeRelayState.OpenRelay:
                    raise Exception(
                        f"Expect OpenRelay as de-energizing event for {self.name}; got {self.de_energizing_event}"
                    )
                self.de_energized_state = RelayClosedOrOpen.RelayOpen
                self.energized_state = RelayClosedOrOpen.RelayClosed

        elif self.name == H0N.store_charge_discharge_relay:
            self.my_state_enum = StoreFlowRelay
            self.my_event_enum = ChangeStoreFlowRelay
            self.transitions = [
                {
                    "trigger": ChangeStoreFlowRelay.ChargeStore,
                    "source": StoreFlowRelay.DischargingStore,
                    "dest": StoreFlowRelay.ChargingStore,
                },
                {
                    "trigger": ChangeStoreFlowRelay.ChargeStore,
                    "source": StoreFlowRelay.ChargingStore,
                    "dest": StoreFlowRelay.ChargingStore,
                },
                {
                    "trigger": ChangeStoreFlowRelay.DischargeStore,
                    "source": StoreFlowRelay.ChargingStore,
                    "dest": StoreFlowRelay.DischargingStore,
                },
                {
                    "trigger": ChangeStoreFlowRelay.DischargeStore,
                    "source": StoreFlowRelay.DischargingStore,
                    "dest": StoreFlowRelay.DischargingStore,
                },
            ]
            if self.de_energizing_event != ChangeStoreFlowRelay.DischargeStore:
                raise Exception(
                    f"Expect DischargeStore as de-energizing event for {self.name}; got {self.de_energizing_event}"
                )
            self.de_energized_state = StoreFlowRelay.DischargingStore
            self.energized_state = StoreFlowRelay.ChargingStore

        elif self.name == H0N.hp_failsafe_relay:
            self.my_state_enum = HeatPumpControl
            self.my_event_enum = ChangeHeatPumpControl
            self.transitions = [
                {
                    "trigger": ChangeHeatPumpControl.SwitchToScada,
                    "source": HeatPumpControl.BufferTankAquastat,
                    "dest": HeatPumpControl.Scada,
                },
                {
                    "trigger": ChangeHeatPumpControl.SwitchToScada,
                    "source": HeatPumpControl.Scada,
                    "dest": HeatPumpControl.Scada,
                },
                {
                    "trigger": ChangeHeatPumpControl.SwitchToTankAquastat,
                    "source": HeatPumpControl.Scada,
                    "dest": HeatPumpControl.BufferTankAquastat,
                },
                {
                    "trigger": ChangeHeatPumpControl.SwitchToTankAquastat,
                    "source": HeatPumpControl.BufferTankAquastat,
                    "dest": HeatPumpControl.BufferTankAquastat,
                },
            ]
            if self.de_energizing_event != ChangeHeatPumpControl.SwitchToTankAquastat:
                raise Exception(
                    f"Expect SwitchToTankAquastat as de-energizing event for {self.name}; got {self.de_energizing_event}"
                )
            self.de_energized_state = HeatPumpControl.BufferTankAquastat
            self.energized_state = HeatPumpControl.Scada

        elif self.name == H0N.aquastat_ctrl_relay:
            self.my_state_enum = AquastatControl
            self.my_event_enum = ChangeAquastatControl
            self.transitions = [
                {
                    "trigger": ChangeAquastatControl.SwitchToScada,
                    "source": AquastatControl.Boiler,
                    "dest": AquastatControl.Scada,
                },
                {
                    "trigger": ChangeAquastatControl.SwitchToScada,
                    "source": AquastatControl.Scada,
                    "dest": AquastatControl.Scada,
                },
                {
                    "trigger": ChangeAquastatControl.SwitchToBoiler,
                    "source": AquastatControl.Scada,
                    "dest": AquastatControl.Boiler,
                },
                {
                    "trigger": ChangeAquastatControl.SwitchToBoiler,
                    "source": AquastatControl.Boiler,
                    "dest": AquastatControl.Boiler,
                },
            ]
            if self.de_energizing_event != ChangeAquastatControl.SwitchToBoiler:
                raise Exception(
                    f"Expect SwitchToBoiler as de-energizing event for {self.name}; got {self.de_energizing_event}"
                )
            self.de_energized_state = AquastatControl.Boiler
            self.energized_state = AquastatControl.Scada

        elif self.name == H0N.primary_pump_failsafe:
            self.my_state_enum = PrimaryPumpControl
            self.my_event_enum = ChangePrimaryPumpControl
            self.transitions = [
                {
                    "trigger": ChangePrimaryPumpControl.SwitchToScada,
                    "source": PrimaryPumpControl.HeatPump,
                    "dest": PrimaryPumpControl.Scada,
                },
                {
                    "trigger": ChangePrimaryPumpControl.SwitchToScada,
                    "source": PrimaryPumpControl.Scada,
                    "dest": PrimaryPumpControl.Scada,
                },
                {
                    "trigger": ChangePrimaryPumpControl.SwitchToHeatPump,
                    "source": PrimaryPumpControl.Scada,
                    "dest": PrimaryPumpControl.HeatPump,
                },
                {
                    "trigger": ChangePrimaryPumpControl.SwitchToHeatPump,
                    "source": PrimaryPumpControl.HeatPump,
                    "dest": PrimaryPumpControl.HeatPump,
                },
            ]
            if self.de_energizing_event != ChangePrimaryPumpControl.SwitchToHeatPump:
                raise Exception(
                    f"Expect SwitchToHeatPump as de-energizing event for {self.name}; got {self.de_energizing_event}"
                )
            self.de_energized_state = PrimaryPumpControl.HeatPump
            self.energized_state = PrimaryPumpControl.Scada
        else:
            raise Exception(f"Unknown relay {self.name}!")
        self.machine = Machine(
            model=self,
            states=self.my_state_enum.values(),
            transitions=self.transitions,
            initial=self.de_energized_state,
            send_event=True,
        )

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)

