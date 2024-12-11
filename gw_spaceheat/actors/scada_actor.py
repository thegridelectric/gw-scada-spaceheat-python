import uuid
import time
from typing import Any, cast
from pydantic import ValidationError
from actors.config import ScadaSettings
from gwproactor import Actor, ServicesInterface
from gwproto import Message
from gwproto.enums import ChangeRelayState, ChangeStoreFlowRelay
from data_classes.house_0_layout import House0Layout
from data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from named_types import FsmEvent


class ScadaActor(Actor):
    layout: House0Layout
    node: ShNode

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)

    @property
    def node(self) -> ShNode:
        # note: self._node exists in proactor but may be stale
        return self.layout.node(self.name)

    @property
    def layout(self) -> House0Layout:
        try:
            layout = cast(House0Layout, self.services.hardware_layout)
        except Exception as e:
            raise Exception(f"Failed to cast layout as House0Layout!! {e}")
        return layout

    @property
    def settings(self) -> ScadaSettings:
        return self.services.settings

    @property
    def primary_scada(self) -> ShNode:
        return self.layout.node(H0N.primary_scada)
    
    @property
    def atomic_ally(self) -> ShNode:
        return self.layout.node(H0N.atomic_ally)
    
    @property
    def synth_generator(self) -> ShNode:
        return self.layout.node(H0N.synth_generator)
    
    ################################
    # Relays
    ################################

    @property
    def vdc_relay(self) -> ShNode:
        return self.layout.node(H0N.vdc_relay)
    
    @property
    def tstat_common_relay(self) -> ShNode:
        return self.layout.node(H0N.tstat_common_relay)

    @property
    def store_charge_discharge_relay(self) -> ShNode:
        return self.layout.node(H0N.store_charge_discharge_relay)
    
    @property
    def hp_failsafe_relay(self) -> ShNode:
        return self.layout.node(H0N.hp_failsafe_relay)
    
    @property
    def hp_scada_ops_relay(self) -> ShNode:
        return self.layout.node(H0N.hp_scada_ops_relay)

    @property
    def aquastat_control_relay(self) -> ShNode:
        return self.layout.node(H0N.aquastat_ctrl_relay)
    
    @property
    def store_pump_failsafe(self) -> ShNode:
        return self.layout.node(H0N.store_pump_failsafe)
    
    ###############################
    # Relay controls
    ################################

    def valved_to_discharge_store(self) -> None:
        """
        Set valves to discharge store (de-energizing) store_charge_discharge_relay (3).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def valved_to_charge_store(self) -> None:
        """
        Set valves to charge store (energizing) store_charge_discharge_relay (3).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")
    

    def turn_on_HP(self) -> None:
        """
        Turn on heat pump by closing (de-energizing) hp_scada_ops_relay (6).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_off_HP(self) -> None:
        """
        Turn off heat pump by opening (energizing) hp_scada_ops_relay (6).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_on_store_pump(self) -> None:
        """
        Turn on the store pump by closing (energizing) store_pump_failsafe relay (9).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_off_store_pump(self) -> None:
        """
        Turn off the store pump by opening (de-energizing) store_pump_failsafe relay (9).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
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
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def boss(self) -> ShNode:
        if ".".join(self.node.handle.split(".")[:-1]) == "":
            return self.node

        boss_handle = ".".join(self.node.handle.split(".")[:-1])
        return next(n for n in self.layout.nodes.values() if n.handle == boss_handle)

    def is_boss_of(self, node: ShNode) -> bool:
        immediate_boss = ".".join(node.Handle.split(".")[:-1])
        return immediate_boss == self.node.handle

    def direct_reports(self) -> list[ShNode]:
        return [n for n in self.layout.nodes.values() if self.is_boss_of(n)]

    def _send_to(self, dst: ShNode, payload: Any) -> None:
        if dst is None:
            return
        message = Message(Src=self.name, Dst=dst.name, Payload=payload)
        if dst.name in set(self.services._communicators.keys()) | {
            self.services.name
        }:  # noqa: SLF001
            self.services.send(message)
        elif dst.Name == H0N.admin:
            self.services._links.publish_message(
                self.services.ADMIN_MQTT, message
            )  # noqa: SLF001
        elif dst.Name == H0N.atn:
            self.services._links.publish_upstream(payload)  # noqa: SLF001
        else:
            self.services._links.publish_message(
                self.services.LOCAL_MQTT, message
            )  # noqa: SLF001

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)
