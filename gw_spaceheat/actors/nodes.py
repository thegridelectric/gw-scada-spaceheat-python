"""(Mostly) static functions describing ShNodes that were in Actor/ActorBase Scada/ScadaBase.

This will probably be refactored as we implement our local registry. Currently separated out here for clarity
because content is static (except for needing a path to the houses.json file, which we should be able to do
away with).
"""

import json
import os
import typing
from functools import cached_property
from typing import List

from config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from drivers.power_meter.power_meter_driver import PowerMeterDriver
from drivers.power_meter.schneiderelectric_iem3455__power_meter_driver import (
    SchneiderElectricIem3455_PowerMeterDriver,
)
from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.make_model.spaceheat_make_model_100 import MakeModel
from schema.enums.role.sh_node_role_110 import Role
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName


class Nodes:
    settings: ScadaSettings

    def __init__(self, settings: ScadaSettings):
        self.settings = settings
        self.settings.dna = json.loads(settings.dna_type)

    @classmethod
    def all_power_tuples(cls) -> List[TelemetryTuple]:
        telemetry_tuples = []
        for node in cls.all_metered_nodes():
            telemetry_tuples += [
                TelemetryTuple(
                    AboutNode=node,
                    SensorNode=cls.power_meter_node(),
                    TelemetryName=TelemetryName.POWER_W,
                )
            ]
        return telemetry_tuples

    @classmethod
    def all_metered_nodes(cls) -> List[ShNode]:
        """All nodes whose power level is metered and included in power reporting by the Scada"""
        return cls.all_resistive_heaters()

    @classmethod
    def all_power_meter_telemetry_tuples(cls) -> List[TelemetryTuple]:
        telemetry_tuples = []
        for about_node in cls.all_metered_nodes():
            for telemetry_name in cls.power_meter_node().component.cac.telemetry_name_list():
                telemetry_tuples.append(
                    TelemetryTuple(
                        AboutNode=about_node,
                        SensorNode=cls.power_meter_node(),
                        TelemetryName=telemetry_name,
                    )
                )
        return telemetry_tuples

    @classmethod
    def power_meter_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        nodes = list(filter(lambda x: x.role == Role.POWER_METER, ShNode.by_alias.values()))
        return nodes[0]

    @classmethod
    def all_resistive_heaters(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.BOOST_ELEMENT), all_nodes))

    @classmethod
    def power_meter_driver(cls) -> PowerMeterDriver:
        component: ElectricMeterComponent = typing.cast(
            ElectricMeterComponent, cls.power_meter_node().component
        )
        cac = component.cac
        if cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver = UnknownPowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            driver = SchneiderElectricIem3455_PowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMPM1:
            driver = GridworksSimPm1_PowerMeterDriver(component=component)
        else:
            raise NotImplementedError(
                f"No ElectricMeter driver yet for {cac.make_model}"
            )
        return driver

    @classmethod
    def power_meter_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        nodes = list(
            filter(lambda x: x.role == Role.POWER_METER, ShNode.by_alias.values())
        )
        return nodes[0]

    @classmethod
    def scada_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role Scada"""
        nodes = list(filter(lambda x: x.role == Role.SCADA, ShNode.by_alias.values()))
        return nodes[0]

    @classmethod
    def home_alone_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role HomeAlone"""
        nodes = list(
            filter(lambda x: x.role == Role.HOME_ALONE, ShNode.by_alias.values())
        )
        return nodes[0]

    @cached_property
    def atn_g_node_alias(self):
        my_atn_as_dict = self.settings.dna["MyAtomicTNodeGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def atn_g_node_id(self):
        my_atn_as_dict = self.settings.dna["MyAtomicTNodeGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def terminal_asset_g_node_alias(self):
        my_atn_as_dict = self.settings.dna["MyTerminalAssetGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def terminal_asset_g_node_id(self):
        my_atn_as_dict = self.settings.dna["MyTerminalAssetGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def scada_g_node_alias(self):
        my_scada_as_dict = self.settings.dna["MyScadaGNode"]
        return my_scada_as_dict["Alias"]

    @cached_property
    def scada_g_node_id(self):
        my_scada_as_dict = self.settings.dna["MyScadaGNode"]
        return my_scada_as_dict["GNodeId"]

    @classmethod
    def my_home_alone(cls) -> ShNode:
        all_nodes = list(ShNode.by_alias.values())
        home_alone_nodes = list(
            filter(lambda x: (x.role == Role.HOME_ALONE), all_nodes)
        )
        if len(home_alone_nodes) != 1:
            raise Exception(
                "there should be a single SpaceheatNode with role HomeAlone"
            )
        return home_alone_nodes[0]

    @classmethod
    def my_boolean_actuators(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.BOOLEAN_ACTUATOR), all_nodes))

    @classmethod
    def my_simple_sensors(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(
            filter(
                lambda x: (
                    x.role == Role.TANK_WATER_TEMP_SENSOR
                    or x.role == Role.BOOLEAN_ACTUATOR
                    or x.role == Role.PIPE_TEMP_SENSOR
                    or x.role == Role.PIPE_FLOW_METER
                ),
                all_nodes,
            )
        )

    @classmethod
    def my_multipurpose_sensors(cls) -> List[ShNode]:
        """This will be a list of all sensing devices that either measure more
        than one ShNode or measure more than one physical quantity type (or both).
        This includes the (unique) power meter, but may also include other roles like thermostats
        and heat pumps."""
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.POWER_METER), all_nodes))

    @classmethod
    def my_telemetry_tuples(cls) -> List[TelemetryTuple]:
        """This will include telemetry tuples from all the multipurpose sensors, the most
        important of which is the power meter."""
        return cls.all_power_meter_telemetry_tuples()
