"""(Mostly) static functions describing ShNodes that were in Actor/ActorBase Scada/ScadaBase.

This will probably be refactored as we implement our local registry. Currently separated out here for clarity
because content is static (except for needing a path to the houses.json file, which we should be able to do
away with).
"""
import copy
import json
import typing
from typing import List, Any, Optional
from functools import cached_property
from pathlib import Path

from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.errors import DataClassLoadingError
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums import Role
from schema.enums import ActorClass
from schema.enums import TelemetryName
from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from helpers import camel_to_snake
from schema.gt.cacs import (
    GtBooleanActuatorCac_Maker,
)
from schema.gt.components import (
    GtBooleanActuatorComponent_Maker,
)

from schema.gt.cacs import ResistiveHeaterCacGt_Maker
from schema.gt.components import (
    ResistiveHeaterComponentGt_Maker,
)

from schema.gt.cacs import GtElectricMeterCac_Maker
from schema.gt.components import (
    GtElectricMeterComponent_Maker,
)
from schema.gt.cacs import (
    GtPipeFlowSensorCac_Maker,
)
from schema.gt.components import (
    GtPipeFlowSensorComponent_Maker,
)
from schema.gt.components import (
    MultipurposeSensorComponentGt_Maker,
)
from schema.gt.cacs import MultipurposeSensorCacGt_Maker
from schema.gt.cacs import SimpleTempSensorCacGt_Maker
from schema.gt.components import (
    SimpleTempSensorComponentGt_Maker,
)
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import SpaceheatNodeGt_Maker


def load_cacs(layout):
    for d in layout["BooleanActuatorCacs"]:
        GtBooleanActuatorCac_Maker.dict_to_dc(d)
    for d in layout["ResistiveHeaterCacs"]:
        ResistiveHeaterCacGt_Maker.dict_to_dc(d)
    for d in layout["ElectricMeterCacs"]:
        GtElectricMeterCac_Maker.dict_to_dc(d)
    for d in layout["PipeFlowSensorCacs"]:
        GtPipeFlowSensorCac_Maker.dict_to_dc(d)
    for d in layout["MultipurposeSensorCacs"]:
        MultipurposeSensorCacGt_Maker.dict_to_dc(d)
    for d in layout["SimpleTempSensorCacs"]:
        SimpleTempSensorCacGt_Maker.dict_to_dc(d)
    for d in layout["OtherCacs"]:
        ComponentAttributeClass(component_attribute_class_id=d["ComponentAttributeClassId"])


def load_components(layout):
    for d in layout["BooleanActuatorComponents"]:
        print(d["ComponentId"])
        GtBooleanActuatorComponent_Maker.dict_to_dc(d)
    for d in layout["ResistiveHeaterComponents"]:
        print(d["ComponentId"])
        ResistiveHeaterComponentGt_Maker.dict_to_dc(d)
    for d in layout["ElectricMeterComponents"]:
        print(d["ComponentId"])
        GtElectricMeterComponent_Maker.dict_to_dc(d)
    for d in layout["PipeFlowSensorComponents"]:
        print(d["ComponentId"])
        GtPipeFlowSensorComponent_Maker.dict_to_dc(d)
    for d in layout["MultipurposeSensorComponents"]:
        print(d["ComponentId"])
        MultipurposeSensorComponentGt_Maker.dict_to_dc(d)
    for d in layout["SimpleTempSensorComponents"]:
        print(d["ComponentId"])
        SimpleTempSensorComponentGt_Maker.dict_to_dc(d)
    for camel in layout["OtherComponents"]:
        print(camel["ComponentId"])
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        Component(**snake_dict)


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
    def load(cls, layout_path: Path | str, included_node_names: Optional[set[str]] = None) -> "HardwareLayout":
        with Path(layout_path).open() as f:
            layout: dict = json.loads(f.read())
        return cls.load_dict(layout, included_node_names=included_node_names)

    @classmethod
    def load_dict(cls, layout: dict, included_node_names: Optional[set[str]] = None) -> "HardwareLayout":
        # TODO layout into GwTuple of a schema type with lots of consistency checking
        load_cacs(layout=layout)
        load_components(layout=layout)
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
                    TelemetryName=TelemetryName.POWER_W,
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
        power_meter_node = list(filter(lambda x: x.role == Role.POWER_METER, self.nodes.values()))[0]
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
        return list(filter(lambda x: (x.role == Role.BOOST_ELEMENT), all_nodes))

    @cached_property
    def power_meter_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        nodes = list(
            filter(lambda x: x.role == Role.POWER_METER, self.nodes.values())
        )
        return nodes[0]

    @cached_property
    def scada_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role Scada"""
        nodes = list(filter(lambda x: x.role == Role.SCADA, self.nodes.values()))
        return nodes[0]

    @cached_property
    def home_alone_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role HomeAlone"""
        nodes = list(
            filter(lambda x: x.role == Role.HOME_ALONE, self.nodes.values())
        )
        return nodes[0]

    @cached_property
    def my_home_alone(self) -> ShNode:
        all_nodes = list(self.nodes.values())
        home_alone_nodes = list(
            filter(lambda x: (x.role == Role.HOME_ALONE), all_nodes)
        )
        if len(home_alone_nodes) != 1:
            raise Exception(
                "there should be a single SpaceheatNode with role HomeAlone"
            )
        return home_alone_nodes[0]

    @cached_property
    def my_boolean_actuators(self) -> List[ShNode]:
        all_nodes = list(self.nodes.values())
        return list(filter(lambda x: (x.role == Role.BOOLEAN_ACTUATOR), all_nodes))

    @cached_property
    def my_simple_sensors(self) -> List[ShNode]:
        all_nodes = list(self.nodes.values())
        return list(
            filter(
                lambda x: (
                    x.actor_class == ActorClass.SIMPLE_SENSOR
                    or x.actor_class == ActorClass.BOOLEAN_ACTUATOR
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
                    x.actor_class == ActorClass.MULTIPURPOSE_SENSOR
                    and hasattr(x, "config_list")
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
        multi_purpose_roles = [Role.POWER_METER, Role.MULTI_CHANNEL_ANALOG_TEMP_SENSOR]
        return list(filter(lambda x: (x.role in multi_purpose_roles), all_nodes))

    @cached_property
    def my_telemetry_tuples(self) -> List[TelemetryTuple]:
        """This will include telemetry tuples from all the multipurpose sensors, the most
        important of which is the power meter."""
        return self.all_power_meter_telemetry_tuples + self.all_multipurpose_telemetry_tuples
