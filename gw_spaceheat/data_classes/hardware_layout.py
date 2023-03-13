"""(Mostly) static functions describing ShNodes that were in Actor/ActorBase Scada/ScadaBase.

This will probably be refactored as we implement our local registry. Currently separated out here for clarity
because content is static (except for needing a path to the houses.json file, which we should be able to do
away with).
"""
import copy
import json
import re
import typing
from dataclasses import dataclass
from typing import List, Any, Optional
from functools import cached_property
from pathlib import Path

from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.errors import DataClassLoadingError
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from enums import Role
from enums import ActorClass
from enums import TelemetryName
from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from schema import GtBooleanActuatorCac_Maker
from schema import GtBooleanActuatorComponent_Maker


from schema import ResistiveHeaterCacGt_Maker
from schema import ResistiveHeaterComponentGt_Maker

from schema import GtElectricMeterCac_Maker
from schema import GtElectricMeterComponent_Maker

from schema import PipeFlowSensorCacGt_Maker

from schema import PipeFlowSensorComponentGt_Maker

from schema.multipurpose_sensor_component_gt import (
    MultipurposeSensorComponentGt_Maker,
)
from schema import MultipurposeSensorCacGt_Maker
from schema import SimpleTempSensorCacGt_Maker
from schema import SimpleTempSensorComponentGt_Maker
from schema import SpaceheatNodeGt_Maker

snake_add_underscore_to_camel_pattern = re.compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(name):
    return snake_add_underscore_to_camel_pattern.sub("_", name).lower()


@dataclass
class LoadError:
    type_name: str
    src_dict: dict
    exception: Exception


def load_cacs(layout: dict, raise_errors: bool = True) -> list[LoadError]:
    errors: list[LoadError] = []
    for type_name, maker_class in [
        ("BooleanActuatorCacs", GtBooleanActuatorCac_Maker),
        ("ResistiveHeaterCacs", ResistiveHeaterCacGt_Maker),
        ("ElectricMeterCacs", GtElectricMeterCac_Maker),
        ("PipeFlowSensorCacs", PipeFlowSensorCacGt_Maker),
        ("MultipurposeSensorCacs", MultipurposeSensorCacGt_Maker),
        ("SimpleTempSensorCacs", SimpleTempSensorCacGt_Maker),
    ]:
        for d in layout[type_name]:
            try:
                maker_class.dict_to_dc(d)
            except Exception as e:
                if raise_errors:
                    raise e
                errors.append(LoadError(type_name, d, e))
    for d in layout["OtherCacs"]:
        try:
            ComponentAttributeClass(
                component_attribute_class_id=d["ComponentAttributeClassId"]
            )
        except Exception as e:
            if raise_errors:
                raise e
            errors.append(LoadError("OtherCacs", d, e))
    return errors


def load_components(layout: dict, raise_errors: bool = True) -> list[LoadError]:
    errors: list[LoadError] = []
    for type_name, maker_class in [
        ("BooleanActuatorComponents", GtBooleanActuatorComponent_Maker),
        ("ResistiveHeaterComponents", ResistiveHeaterComponentGt_Maker),
        ("ElectricMeterComponents", GtElectricMeterComponent_Maker),
        ("PipeFlowSensorComponents", PipeFlowSensorComponentGt_Maker),
        ("MultipurposeSensorComponents", MultipurposeSensorComponentGt_Maker),
        ("SimpleTempSensorComponents", SimpleTempSensorComponentGt_Maker),
    ]:
        for d in layout[type_name]:
            try:
                maker_class.dict_to_dc(d)
            except Exception as e:
                if raise_errors:
                    raise e
                errors.append(LoadError(type_name, d, e))
        for camel in layout["OtherComponents"]:
            try:
                snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
                Component(**snake_dict)
            except Exception as e:
                if raise_errors:
                    raise e
                errors.append(LoadError(type_name, camel, e))
    return errors

class HardwareLayout:
    layout: dict
    cacs: dict[str, ComponentAttributeClass]
    components: dict[str, Component]
    nodes: dict[str, ShNode]

    def __init__(self, layout: dict, included_node_names: Optional[set[str]] = None):
        self.layout = copy.deepcopy(layout)
        self.cacs = dict(ComponentAttributeClass.by_id)
        self.components = dict(Component.by_id)
        self.nodes = {
            node_dict["Alias"]: SpaceheatNodeGt_Maker.dict_to_dc(node_dict)
            for node_dict in self.layout["ShNodes"]
            if included_node_names is None or node_dict["Alias"] in included_node_names
        }

    @classmethod
    def load(
        cls,
        layout_path: Path | str,
        included_node_names: Optional[set[str]] = None,
        raise_errors: bool = True,
        errors: Optional[list[LoadError]] = None,
    ) -> "HardwareLayout":
        with Path(layout_path).open() as f:
            layout: dict = json.loads(f.read())
        return cls.load_dict(
            layout,
            included_node_names=included_node_names,
            raise_errors=raise_errors,
            errors=errors
        )

    @classmethod
    def load_dict(
        cls,
        layout: dict,
        included_node_names: Optional[set[str]] = None,
        raise_errors: bool = True,
        errors: Optional[list[LoadError]] = None,
    ) -> "HardwareLayout":
        if errors is None:
            errors = []
        errors.extend(load_cacs(layout=layout, raise_errors=raise_errors))
        errors.extend(load_components(layout=layout, raise_errors=raise_errors))
        return HardwareLayout(layout, included_node_names=included_node_names)

    def node(self, alias: str, default: Any = None) -> ShNode:
        return self.nodes.get(alias, default)

    def component(self, alias: str) -> Optional[Component]:
        return self.component_from_node(self.node(alias, None))

    def cac(self, alias: str) -> Optional[ComponentAttributeClass]:
        return self.cac_from_component(self.component(alias))

    def component_from_node(self, node: Optional[ShNode]) -> Optional[Component]:
        return self.components.get(node.component_id if node is not None else None, None)

    def cac_from_component(self, component: Optional[Component]) -> Optional[ComponentAttributeClass]:
        return self.cacs.get(component.component_attribute_class_id if component is not None else None, None)

    @classmethod
    def parent_alias(cls, alias: str) -> str:
        last_delimiter = alias.rfind(".")
        if last_delimiter == -1:
            return ""
        else:
            return alias[:last_delimiter]

    def parent_node(self, alias: str) -> Optional[ShNode]:
        parent_alias = self.parent_alias(alias)
        if not parent_alias:
            return None
        else:
            if parent_alias not in self.nodes:
                raise DataClassLoadingError(f"{alias} is missing parent {parent_alias}!")
            return self.node(parent_alias)

    def descendants(self, alias: str) -> List[ShNode]:
        return list(filter(lambda x: x.alias.startswith(alias), self.nodes.values()))

    @cached_property
    def atn_g_node_alias(self):
        return self.layout["MyAtomicTNodeGNode"]["Alias"]

    @cached_property
    def atn_g_node_instance_id(self):
        return self.layout["MyAtomicTNodeGNode"]["GNodeId"]

    @cached_property
    def atn_g_node_id(self):
        return self.layout["MyAtomicTNodeGNode"]["GNodeId"]

    @cached_property
    def terminal_asset_g_node_alias(self):
        my_atn_as_dict = self.layout["MyTerminalAssetGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def terminal_asset_g_node_id(self):
        my_atn_as_dict = self.layout["MyTerminalAssetGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def scada_g_node_alias(self):
        my_scada_as_dict = self.layout["MyScadaGNode"]
        return my_scada_as_dict["Alias"]

    @cached_property
    def scada_g_node_id(self):
        my_scada_as_dict = self.layout["MyScadaGNode"]
        return my_scada_as_dict["GNodeId"]

    @cached_property
    def all_power_tuples(self) -> List[TelemetryTuple]:
        telemetry_tuples = []
        for node in self.all_metered_nodes:
            telemetry_tuples += [
                TelemetryTuple(
                    AboutNode=node,
                    SensorNode=self.power_meter_node,
                    TelemetryName=TelemetryName.PowerW,
                )
            ]
        return telemetry_tuples

    @cached_property
    def all_metered_nodes(self) -> List[ShNode]:
        """All nodes whose power level is metered and included in power reporting by the Scada"""
        return self.all_resistive_heaters

    @cached_property
    def all_power_meter_telemetry_tuples(self) -> List[TelemetryTuple]:
        telemetry_names = self.power_meter_cac.telemetry_name_list()
        telemetry_tuples = []
        for about_node in self.all_metered_nodes:
            for telemetry_name in telemetry_names:
                telemetry_tuples.append(
                    TelemetryTuple(
                        AboutNode=about_node,
                        SensorNode=self.power_meter_node,
                        TelemetryName=telemetry_name,
                    )
                )
        return telemetry_tuples

    @cached_property
    def power_meter_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        power_meter_node = list(filter(lambda x: x.role == Role.PowerMeter, self.nodes.values()))[0]
        return power_meter_node

    @cached_property
    def power_meter_component(self) -> Component:
        if self.power_meter_node.component is None:
            raise ValueError(f"ERROR. power_meter_node {self.power_meter_node} has no component.")
        return self.power_meter_node.component

    @cached_property
    def power_meter_cac(self) -> ElectricMeterCac:
        if not isinstance(self.power_meter_component.component_attribute_class, ElectricMeterCac):
            raise ValueError(
                f"ERROR. power_meter_component cac {self.power_meter_component.component_attribute_class}"
                f" / {type(self.power_meter_component.component_attribute_class)} is not an ElectricMeterCac"
            )
        return typing.cast(
            ElectricMeterCac,
            self.power_meter_node.component.component_attribute_class
        )

    @cached_property
    def all_resistive_heaters(self) -> List[ShNode]:
        all_nodes = list(self.nodes.values())
        return list(filter(lambda x: (x.role == Role.BoostElement), all_nodes))

    @cached_property
    def power_meter_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        nodes = list(
            filter(lambda x: x.role == Role.PowerMeter, self.nodes.values())
        )
        return nodes[0]

    @cached_property
    def scada_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role Scada"""
        nodes = list(filter(lambda x: x.role == Role.Scada, self.nodes.values()))
        return nodes[0]

    @cached_property
    def home_alone_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role HomeAlone"""
        nodes = list(
            filter(lambda x: x.role == Role.HomeAlone, self.nodes.values())
        )
        return nodes[0]

    @cached_property
    def my_home_alone(self) -> ShNode:
        all_nodes = list(self.nodes.values())
        home_alone_nodes = list(
            filter(lambda x: (x.role == Role.HomeAlone), all_nodes)
        )
        if len(home_alone_nodes) != 1:
            raise Exception(
                "there should be a single SpaceheatNode with role HomeAlone"
            )
        return home_alone_nodes[0]

    @cached_property
    def my_boolean_actuators(self) -> List[ShNode]:
        all_nodes = list(self.nodes.values())
        return list(filter(lambda x: (x.role == Role.BooleanActuator), all_nodes))

    @cached_property
    def my_simple_sensors(self) -> List[ShNode]:
        all_nodes = list(self.nodes.values())
        return list(
            filter(
                lambda x: (
                    x.actor_class == ActorClass.SimpleSensor
                    or x.actor_class == ActorClass.BooleanActuator
                ),
                all_nodes,
            )
        )

    @cached_property
    def all_multipurpose_telemetry_tuples(self) -> List[TelemetryTuple]:
        all_nodes = list(self.nodes.values())
        multi_nodes = list(
            filter(
                lambda x: (
                    x.actor_class == ActorClass.MultipurposeSensor
                    and hasattr(x.component, "config_list")
                ),
                all_nodes
            )
        )
        telemetry_tuples = []
        for node in multi_nodes:
            for config in getattr(node.component, "config_list"):
                about_node = self.node(config.AboutNodeName)
                telemetry_tuples.append(
                    TelemetryTuple(
                        AboutNode=about_node,
                        SensorNode=node,
                        TelemetryName=config.TelemetryName,
                    )
                )
        return telemetry_tuples

    @cached_property
    def my_multipurpose_sensors(self) -> List[ShNode]:
        """This will be a list of all sensing devices that either measure more
        than one ShNode or measure more than one physical quantity type (or both).
        This includes the (unique) power meter, but may also include other roles like thermostats
        and heat pumps."""
        all_nodes = list(self.nodes.values())
        multi_purpose_roles = [Role.PowerMeter, Role.MultiChannelAnalogTempSensor]
        return list(filter(lambda x: (x.role in multi_purpose_roles), all_nodes))

    @cached_property
    def my_telemetry_tuples(self) -> List[TelemetryTuple]:
        """This will include telemetry tuples from all the multipurpose sensors, the most
        important of which is the power meter."""
        return self.all_power_meter_telemetry_tuples + self.all_multipurpose_telemetry_tuples
