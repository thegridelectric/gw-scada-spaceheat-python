import time
import uuid
from typing import Any, Dict, List, Optional, cast

from actors.config import ScadaSettings
from actors.scada_data import ScadaData
from data_classes.house_0_layout import House0Layout
from data_classes.house_0_names import H0N, House0RelayIdx
from gw.errors import DcError
from gwproactor import Actor, ServicesInterface, QOS
from gwproto import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (
    ActorClass,
    ChangeAquastatControl,
    ChangeHeatcallSource,
    ChangeHeatPumpControl,
    ChangePrimaryPumpControl,
    ChangeRelayState,
    ChangeStoreFlowRelay,
    RelayClosedOrOpen
)
from enums import TurnHpOnOff
from named_types import FsmEvent
from pydantic import ValidationError


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
    def data(self) -> ScadaData:
        return self._services.data

    @property
    def atn(self) -> ShNode:
        return self.layout.node(H0N.atn)

    @property
    def primary_scada(self) -> ShNode:
        return self.layout.node(H0N.primary_scada)

    @property
    def atomic_ally(self) -> ShNode:
        return self.layout.node(H0N.atomic_ally)

    @property
    def home_alone(self) -> ShNode:
        return self.layout.node(H0N.home_alone)
    
    @property
    def synth_generator(self) -> ShNode:
        return self.layout.node(H0N.synth_generator)

    @property
    def strat_boss(self) -> ShNode:
        return self.layout.node(H0N.strat_boss)

    @property
    def hp_relay_boss(self) -> ShNode:
        return self.layout.node(H0N.hp_relay_boss)

    def my_actuators(self) -> List[ShNode]:
        """Get all actuator nodes that are descendants of this node in the handle hierarchy"""
        my_handle_prefix = f"{self.node.handle}."
        return [
            node for node in self.layout.actuators
            if node.handle.startswith(my_handle_prefix)
        ]


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

    @property
    def primary_pump_failsafe(self) -> ShNode:
        return self.layout.node(H0N.primary_pump_failsafe)

    @property
    def primary_pump_scada_ops(self) -> ShNode:
        return self.layout.node(H0N.primary_pump_scada_ops)

    def stat_failsafe_relay(self, zone: str) -> ShNode:
        """
        Returns the failsafe relay for the zone.
        Raises a DcError if zone is not in the layout's zone_list
        """
        try:
            i = self.layout.zone_list.index(zone)
        except ValueError as e:
            raise DcError(
                f"Called stat_failsafe_relay for {zone} which does not exist!"
            ) from e
        failsafe_idx = House0RelayIdx.base_stat + 2 * i
        stat_failsafe_name = f"relay{failsafe_idx}"
        return self.layout.node(stat_failsafe_name)

    def stat_ops_relay(self, zone: str) -> ShNode:
        """
        Returns the scada thermostat ops relay for the zone
        Raises a DcError if zone is not in the layout's zone_list
        """
        try:
            i = self.layout.zone_list.index(zone)
        except ValueError as e:
            raise Exception(
                f"Called stat_failsafe_relay for {zone} which does not exist!"
            ) from e
        ops_idx = House0RelayIdx.base_stat + 2 * i + 1
        stat_ops_name = f"relay{ops_idx}"
        return self.layout.node(stat_ops_name)

    ###############################
    # Relay controls
    ################################

    def de_energize(self, relay: ShNode, from_node=None) -> None:
        if relay.ActorClass != ActorClass.Relay:
            self.log(f"Can only energize relays! ignoring energize {relay}")
            return
        if relay == self.hp_scada_ops_relay:
            self.log(f"Can only manage HpScadaOps relay {relay.name} via its boss {self.hp_relay_boss.Name}!")
            return
        zone_by_failsafe_relay: Dict[ShNode, str] = {}
        zone_by_ops_relay: Dict[ShNode, str] = {}
        for zone in self.layout.zone_list:
            zone_by_failsafe_relay[self.stat_failsafe_relay(zone)] = zone
            zone_by_ops_relay[self.stat_ops_relay(zone)] = zone
        if relay in zone_by_failsafe_relay:
            self.heatcall_ctrl_to_stat(zone_by_failsafe_relay[relay], from_node)
        elif relay in zone_by_ops_relay:
            self.stat_ops_open_relay(zone_by_ops_relay[relay], from_node)
        elif relay == self.vdc_relay:
            self.close_vdc_relay(from_node)
        elif relay == self.tstat_common_relay:
            self.close_tstat_common_relay(from_node)
        elif relay == self.store_charge_discharge_relay:
            self.valved_to_discharge_store(from_node)
        elif relay == self.hp_failsafe_relay:
            self.hp_failsafe_switch_to_aquastat(from_node)
        elif relay == self.aquastat_control_relay:
            self.aquastat_ctrl_switch_to_boiler(from_node)
        elif relay == self.store_pump_failsafe:
            self.turn_off_store_pump(from_node)
        elif relay == self.primary_pump_failsafe:
            self.primary_pump_failsafe_to_hp(from_node)
        elif relay == self.primary_pump_scada_ops:
            self.turn_off_primary_pump(from_node)
        else:
            self.log(f"Unrecognized relay {relay}! Not energizing")

    def energize(self, relay: ShNode, from_node=None) -> None:
        if relay.ActorClass != ActorClass.Relay:
            self.log(f"Can only energize relays! ignoring energize {relay}")
            return
        if relay == self.hp_scada_ops_relay:
            self.log(f"Can only manage HpScadaOps relay {relay.name} via its boss {self.hp_relay_boss.Name}!")
            return
        zone_by_failsafe_relay: Dict[ShNode, str] = {}
        zone_by_ops_relay: Dict[ShNode, str] = {}
        for zone in self.layout.zone_list:
            zone_by_failsafe_relay[self.stat_failsafe_relay(zone)] = zone
            zone_by_ops_relay[self.stat_ops_relay(zone)] = zone
        if relay in zone_by_failsafe_relay:
            self.heatcall_ctrl_to_scada(zone_by_failsafe_relay[relay], from_node)
        elif zone in zone_by_ops_relay:
            self.stat_ops_close_relay(zone_by_ops_relay[relay], from_node)
        if relay == self.vdc_relay:
            self.open_vdc_relay(from_node)
        elif relay == self.tstat_common_relay:
            self.open_tstat_common_relay(from_node)
        elif relay == self.store_charge_discharge_relay:
            self.valved_to_charge_store(from_node)
        elif relay == self.hp_failsafe_relay:
            self.hp_failsafe_switch_to_scada(from_node)
        elif relay == self.aquastat_control_relay:
            self.aquastat_ctrl_switch_to_scada(from_node)
        elif relay == self.store_pump_failsafe:
            self.turn_on_store_pump(from_node)
        elif relay == self.primary_pump_failsafe:
            self.primary_pump_failsafe_to_scada(from_node)
        elif relay == self.primary_pump_scada_ops:
            self.turn_on_primary_pump(from_node)
        else:
            self.log(f"Unrecognized relay {relay}! Not energizing")

    def close_vdc_relay(self, trigger_id: Optional[str] = None, from_node: Optional[ShNode] = None) -> None:
        """
        Close vdc relay (de-energizing relay 1).
        Will log an error and do nothing if not the boss of this relay
        """
        if trigger_id is None:
            trigger_id = str(uuid.uuid4())
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.vdc_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=trigger_id,
            )
            if from_node is None:
                self._send_to(self.vdc_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.vdc_relay.name,
                            Payload=event))
            self.log(f"CloseRelay to {self.vdc_relay.name}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def open_vdc_relay(self, trigger_id: Optional[str] = None, from_node: Optional[ShNode] = None) -> None:
        """
        Open vdc relay (energizing relay 1).
        Will log an error and do nothing if not the boss of this relay
        """
        if trigger_id is None:
            trigger_id = str(uuid.uuid4())
        try:

            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.vdc_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=trigger_id,
            )
            if from_node is None:
                self._send_to(self.vdc_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.vdc_relay.name,
                            Payload=event))
            self.log(f"OpenRelay to {self.vdc_relay.name}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def close_tstat_common_relay(self, from_node: Optional[ShNode] = None) -> None:
        """
        Close tstat common relay (de-energizing relay 2).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.tstat_common_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.tstat_common_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.tstat_common_relay.name,
                            Payload=event))
            self.log(f"{from_node.handle} sending CloseRelay to {self.tstat_common_relay.handle}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def open_tstat_common_relay(self, from_node: Optional[ShNode] = None) -> None:
        """
        Open tstat common relay (energizing relay 2).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.tstat_common_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.tstat_common_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.tstat_common_relay.name,
                            Payload=event))
            self.log(f"{from_node.handle} sending OpenRelay to {self.tstat_common_relay.handle}")
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def valved_to_discharge_store(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set valves to discharge store (de-energizing) store_charge_discharge_relay (3).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.store_charge_discharge_relay.handle,
                EventType=ChangeStoreFlowRelay.enum_name(),
                EventName=ChangeStoreFlowRelay.DischargeStore,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.store_charge_discharge_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.store_charge_discharge_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending DischargeStore to Store ChargeDischarge {self.store_charge_discharge_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def valved_to_charge_store(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set valves to charge store (energizing) store_charge_discharge_relay (3).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.store_charge_discharge_relay.handle,
                EventType=ChangeStoreFlowRelay.enum_name(),
                EventName=ChangeStoreFlowRelay.ChargeStore,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.store_charge_discharge_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.store_charge_discharge_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending ChargeStore to Store ChargeDischarge {self.store_charge_discharge_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def hp_failsafe_switch_to_aquastat(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set the hp control to Aquastat by de-energizing hp_failsafe_relay (5)
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.hp_failsafe_relay.handle,
                EventType=ChangeHeatPumpControl.enum_name(),
                EventName=ChangeHeatPumpControl.SwitchToTankAquastat,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.hp_failsafe_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.hp_failsafe_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToTankAquastat to Hp Failsafe {self.hp_failsafe_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def hp_failsafe_switch_to_scada(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set the hp control to Scada by energizing hp_failsafe_relay (5)
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.hp_failsafe_relay.handle,
                EventType=ChangeHeatPumpControl.enum_name(),
                EventName=ChangeHeatPumpControl.SwitchToScada,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.hp_failsafe_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.hp_failsafe_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToScada to Hp Failsafe {self.hp_failsafe_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_on_HP(self, from_node: Optional[ShNode] = None) -> None:
        """ Turn on heat pump by sending trigger to HpRelayBoss

        from_node defaults to self.node if no from_node sent.
        Will log an error and do nothing if from_node is not the boss of HpRelayBoss
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.hp_relay_boss.handle,
                EventType= TurnHpOnOff.enum_name(),
                EventName=TurnHpOnOff.TurnOn,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.hp_relay_boss, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.hp_relay_boss.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending CloseRelay to HpRelayBoss {self.hp_relay_boss.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to tell HpRelayBoss to turn on HP but didn't have rights: {e}")

    def turn_off_HP(self, from_node: Optional[ShNode] = None) -> None:
        """  Turn off heat pump by sending trigger to HpRelayBoss
        
        from_node defaults to self.node if no from_node sent.
        Will log an error and do nothing if from_node is not the boss of HpRelayBoss
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.hp_relay_boss.handle,
                EventType=TurnHpOnOff.enum_name(),
                EventName=TurnHpOnOff.TurnOff,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.hp_relay_boss, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.hp_relay_boss.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending OpenRelay to HpRelayBoss {self.hp_relay_boss.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to tell HpRelayBoss to turn off HP but didn't have rights: {e}")

    def aquastat_ctrl_switch_to_boiler(self, from_node: Optional[ShNode] = None) -> None:
        """
        Switch Aquastat ctrl from Scada to boiler by de-energizing aquastat_control_relay (8).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.aquastat_control_relay.handle,
                EventType=ChangeAquastatControl.enum_name(),
                EventName=ChangeAquastatControl.SwitchToBoiler,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.aquastat_control_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.aquastat_control_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToScada to Boiler Ctrl {self.aquastat_control_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def aquastat_ctrl_switch_to_scada(self, from_node: Optional[ShNode] = None) -> None:
        """
        Switch Aquastat ctrl from boiler to Scada by energizing aquastat_control_relay (8).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.aquastat_control_relay.handle,
                EventType=ChangeAquastatControl.enum_name(),
                EventName=ChangeAquastatControl.SwitchToScada,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.aquastat_control_relay, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.aquastat_control_relay.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToScada to Aquastat Ctrl {self.aquastat_control_relay.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_off_store_pump(self, from_node: Optional[ShNode] = None) -> None:
        """
        Turn off the store pump by opening (de-energizing) store_pump_failsafe relay (9).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.store_pump_failsafe.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.store_pump_failsafe, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.store_pump_failsafe.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending OpenRelay to StorePump OnOff {self.store_pump_failsafe.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_on_store_pump(self, from_node: Optional[ShNode] = None) -> None:
        """
        Turn on the store pump by closing (energizing) store_pump_failsafe relay (9).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.store_pump_failsafe.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.store_pump_failsafe, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.store_pump_failsafe.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending CloseRelay to StorePump OnOff {self.store_pump_failsafe.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def primary_pump_failsafe_to_hp(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set heat pump to having direct control over primary pump by de-energizing
        primary_pump_failsafe_relay (12).
        Will log an error and do nothing if not the boss of this relay
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.primary_pump_failsafe.handle,
                EventType=ChangePrimaryPumpControl.enum_name(),
                EventName=ChangePrimaryPumpControl.SwitchToHeatPump,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.primary_pump_failsafe, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.primary_pump_failsafe.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToHeatPump to {self.primary_pump_failsafe.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def primary_pump_failsafe_to_scada(self, from_node: Optional[ShNode] = None) -> None:
        """
        Set Scada to having direct control over primary pump by energizing
        primary_pump_failsafe_relay (12).
        Will log an error and do nothing if not the boss of this relay.
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.primary_pump_failsafe.handle,
                EventType=ChangePrimaryPumpControl.enum_name(),
                EventName=ChangePrimaryPumpControl.SwitchToScada,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.primary_pump_failsafe, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.primary_pump_failsafe.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToHeatPump to {self.primary_pump_failsafe.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_off_primary_pump(self, from_node: Optional[ShNode] = None) -> None:
        """
        Turn off primary pump (if under Scada control) by de-energizing
        primary_pump_scada_ops (11).
        Will log an error and do nothing if not the boss of this relay.
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.primary_pump_scada_ops.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.primary_pump_scada_ops, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.primary_pump_scada_ops.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending OpenRelay to {self.primary_pump_scada_ops.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def turn_on_primary_pump(self, from_node: Optional[ShNode] = None) -> None:
        """
        Turn on primary pump (if under Scada control) by energizing
        primary_pump_scada_ops (11).
        Will log an error and do nothing if not the boss of this relay.
        """
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.primary_pump_scada_ops.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.primary_pump_scada_ops, event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.primary_pump_scada_ops.name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending CloseRelay to {self.primary_pump_scada_ops.handle}"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def heatcall_ctrl_to_scada(self, zone: str, from_node: Optional[ShNode] = None) -> None:
        """
        Take over thermostatic control of the zone from the wall thermostat
        by energizing appropriate relay.
        Will log an error and do nothing if not the boss of this relay.
        """
        if zone not in self.layout.zone_list:
            self.log(f"{zone} not a recongized zone!")
            return
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.stat_failsafe_relay(zone).handle,
                EventType=ChangeHeatcallSource.enum_name(),
                EventName=ChangeHeatcallSource.SwitchToScada,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.stat_failsafe_relay(zone), event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.stat_failsafe_relay(zone).name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToScada to {self.stat_failsafe_relay(zone).handle} (zone {zone})"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def heatcall_ctrl_to_stat(self, zone: str, from_node: Optional[ShNode] = None) -> None:
        """
        Return control of the whitewire heatcall signal to the wall thermostat
        by de-energizing appropriate relay.
        Will log an error and do nothing if not the boss of this relay.
        """
        if zone not in self.layout.zone_list:
            self.log(f"{zone} not a recongized zone!")
            return
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.stat_failsafe_relay(zone).handle,
                EventType=ChangeHeatcallSource.enum_name(),
                EventName=ChangeHeatcallSource.SwitchToWallThermostat,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.stat_failsafe_relay(zone), event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.stat_failsafe_relay(zone).name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending SwitchToWallThermostat to {self.stat_failsafe_relay(zone).handle} (zone {zone})"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def stat_ops_close_relay(self, zone: str, from_node: Optional[ShNode] = None) -> None:
        """
        Close (energize) the ScadaOps relay for associated zone. Will send a heatcall on the white
        wire IF the associated failsafe relay is energized (switched to SCADA).
        Will log an error and do nothing if not the boss of this relay.
        """
        if zone not in self.layout.zone_list:
            self.log(f"{zone} not a recongized zone!")
            return
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.stat_ops_relay(zone).handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.stat_ops_relay(zone), event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.stat_ops_relay(zone).name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending CloseRelay to {self.stat_ops_relay(zone).handle} (zone {zone})"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    def stat_ops_open_relay(self, zone: str, from_node: Optional[ShNode] = None) -> None:
        """
        Open (de-energize) the ScadaOps relay for associated zone. Will send 0 on the white
        wire IF the associated failsafe relay is energized (switched to SCADA).
        Will log an error and do nothing if not the boss of this relay.
        """
        if zone not in self.layout.zone_list:
            self.log(f"{zone} not a recongized zone!")
            return
        try:
            event = FsmEvent(
                FromHandle=self.node.handle if from_node is None else from_node.handle,
                ToHandle=self.stat_ops_relay(zone).handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=str(uuid.uuid4()),
            )
            if from_node is None:
                self._send_to(self.stat_ops_relay(zone), event)
            else:
                self.services.send(
                    Message(Src=from_node.name,
                            Dst=self.stat_ops_relay(zone).name,
                            Payload=event))
            self.log(
                f"{self.node.handle if from_node is None else from_node.handle} sending OpenRelay to {self.stat_ops_relay(zone).handle} (zone {zone})"
            )
        except ValidationError as e:
            self.log(f"Tried to change a relay but didn't have the rights: {e}")

    @property
    def boss(self) -> ShNode:
        if ".".join(self.node.handle.split(".")[:-1]) == "":
            return self.node

        boss_handle = ".".join(self.node.handle.split(".")[:-1])
        return next(n for n in self.layout.nodes.values() if n.handle == boss_handle)

    def the_boss_of(self, node: ShNode) -> Optional[ShNode]:
        if node.Handle == node.Name:
            return None
        boss_name= ".".join(node.Handle.split(".")[-2])
        return self.layout.node(boss_name, None)

    def direct_reports(self) -> list[ShNode]:
        return [n for n in self.layout.nodes.values() if self.is_boss_of(n)]

    def _send_to(self, dst: ShNode, payload: Any, src: Optional[ShNode] = None) -> None:
        if dst is None:
            return
        if src is None:
            src = self.node
        # HACK FOR nodes whose 'actors' are handled by their parent's communicator
        communicator_by_name = {dst.Name: dst.Name}
        communicator_by_name[H0N.home_alone_normal] = H0N.home_alone
        
        message = Message(Src=src.name, Dst=communicator_by_name[dst.Name], Payload=payload)

        if communicator_by_name[dst.name] in set(self.services._communicators.keys()) | {
            self.services.name
        }:  # noqa: SLF001
            self.services.send(message)
        elif dst.Name == H0N.admin:
            self.services._links.publish_message(
                link_name=self.services.ADMIN_MQTT,
                message=Message(
                    Src=self.services.publication_name, Dst=dst.Name, Payload=payload
                ),
                qos=QOS.AtMostOnce,
            ) # noqa: SLF001
        elif dst.Name == H0N.atn:
            self.services._links.publish_upstream(payload)  # noqa: SLF001
        else:
            self.services._links.publish_message(
                self.services.LOCAL_MQTT, message
            )  # noqa: SLF001

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)

    ##########################################
    # Data related
    ##########################################

    def hp_relay_closed(self) -> bool:
        if self.hp_scada_ops_relay.Name not in self.data.latest_machine_state:
            raise Exception("We should know the state of the hp ops relay!")
        if self.data.latest_machine_state[self.hp_scada_ops_relay.Name].State == RelayClosedOrOpen.RelayClosed:
            return True
        return False
