"""Temporary package for assisting generation of hardware_layout.json files"""
import json
import typing
from pathlib import Path
from typing import Optional
import uuid

from gwproto.enums import ActorClass
from gwproto.enums import LocalCommInterface
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import ElectricMeterCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import TelemetryReportingConfig
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from multidict import MultiDict

__all__ = [
    "LayoutDb",
]

class LayoutDb:
    lists: dict[str, list[ComponentAttributeClassGt | ComponentGt | SpaceheatNodeGt]]
    cacs_by_id: dict[str, ComponentAttributeClassGt]
    cacs_by_alias: dict[str, str]
    cacs_by_type: dict[str, str]
    components_by_id: dict[str, ComponentGt]
    components_by_alias: dict[str, str]
    components_by_type: MultiDict
    nodes_by_id: dict[str, SpaceheatNodeGt]
    nodes_by_alias: dict[str, str]
    nodes_by_component: MultiDict
    misc: dict

    def __init__(
        self,
        cacs: Optional[list[ComponentAttributeClassGt]] = None,
        components: Optional[list[ComponentGt]] = None,
        nodes: Optional[list[SpaceheatNodeGt]] = None,
        add_stubs: bool = False,
    ):
        self.lists = {}
        self.cacs_by_id = {}
        self.cacs_by_alias = {}
        self.cacs_by_type = {}
        self.components_by_id = {}
        self.components_by_alias = {}
        self.components_by_type = MultiDict()
        self.component_lists = {}
        self.nodes_by_id = {}
        self.nodes_by_alias = {}
        self.nodes_by_component = MultiDict()
        self.misc = {}
        if cacs is not None:
            self.add_cacs(cacs)
        if components is not None:
            self.add_components(components)
        if nodes is not None:
            self.add_nodes(nodes)
        if add_stubs:
            self.add_stubs()

    def add_cacs(self, cacs:list[ComponentAttributeClassGt], layout_list_name: str = "OtherCacs"):
        for cac in cacs:
            if cac.ComponentAttributeClassId in self.cacs_by_id:
                raise ValueError(
                    f"ERROR: cac with id <{cac.ComponentAttributeClassId}> "
                    "already present"
                )
            if cac.DisplayName in self.cacs_by_alias:
                raise ValueError(
                    f"ERROR: cac with DisplayName <{cac.DisplayName}> "
                    "already present"
                )
            if cac.TypeName in self.cacs_by_type:
                raise ValueError(
                    f"ERROR: cac with TypeName <{cac.TypeName}> "
                    "already present"
                )
            self.cacs_by_id[cac.ComponentAttributeClassId] = cac
            self.cacs_by_alias[cac.DisplayName] = cac.ComponentAttributeClassId
            self.cacs_by_type[cac.TypeName] = cac.ComponentAttributeClassId
            if layout_list_name not in self.lists:
                self.lists[layout_list_name] = []
            self.lists[layout_list_name].append(cac)

    def add_components(self, components:list[ComponentGt], layout_list_name: str = "OtherComponents"):
        for component in components:
            if component.ComponentId in self.components_by_id:
                raise ValueError(
                    f"ERROR. Component with id {component.ComponentId} "
                    "already present."
                )
            if component.DisplayName in self.components_by_alias:
                raise ValueError(
                    f"ERROR. Component with DisplayName {component.DisplayName} "
                    "already present."
                )
            self.components_by_id[component.ComponentId] = component
            self.components_by_alias[component.DisplayName] = component.ComponentId
            self.components_by_type.add(component.TypeName, component.ComponentId)
            if layout_list_name not in self.lists:
                self.lists[layout_list_name] = []
            self.lists[layout_list_name].append(component)

    def add_nodes(self, nodes:list[SpaceheatNodeGt]):
        for node in nodes:
            if node.ShNodeId in self.nodes_by_id:
                raise ValueError(
                    f"ERROR Node id {node.ShNodeId} already present."
                )
            if node.Alias in self.nodes_by_alias:
                raise ValueError(
                    f"ERROR Node alias {node.Alias} already present."
                )
            self.nodes_by_id[node.ShNodeId] = node
            self.nodes_by_alias[node.Alias] = node.ShNodeId
            if node.ComponentId:
                self.nodes_by_component.add(node.ComponentId, node.ShNodeId)
            layout_list_name = "ShNodes"
            if layout_list_name not in self.lists:
                self.lists[layout_list_name] = []
            self.lists[layout_list_name].append(node)

    def cac_id_by_alias(self, cac_alias: str) -> Optional[str]:
        return self.cacs_by_alias.get(cac_alias, None)

    def cac_id_by_type(self, cac_type: str) -> Optional[str]:
        return self.cacs_by_type.get(cac_type, None)

    def component_id_by_alias(self, component_alias: str) -> Optional[str]:
        return self.components_by_alias.get(component_alias, None)

    def component_id_by_type(self, component_type: str) -> Optional[list[str]]:
        return self.components_by_type.get(component_type, None)

    def add_stub_power_meter(self):
        self.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    ElectricMeterCacGt(
                        ComponentAttributeClassId=str(uuid.uuid4()),
                        MakeModel=MakeModel.GRIDWORKS__SIMPM1,
                        DisplayName="Dummy Electric Meter Cac",
                        TelemetryNameList=[TelemetryName.PowerW],
                        Interface=LocalCommInterface.SIMRABBIT,
                        PollPeriodMs=1000,
                    )
                ),
            ],
            "ElectricMeterCacs"
        )
        self.add_components(
            [
                typing.cast(
                    ComponentGt,
                    ElectricMeterComponentGt(
                        ComponentId=str(uuid.uuid4()),
                        ComponentAttributeClassId=self.cac_id_by_alias("Dummy Electric Meter Cac"),
                        DisplayName="Dummy Electric Meter Component",
                        ConfigList=[
                            TelemetryReportingConfig(
                                AboutNodeName="a.elt1",
                                ReportOnChange=True,
                                SamplePeriodS=300,
                                Exponent=1,
                                TelemetryName=TelemetryName.PowerW,
                                Unit=Unit.W,
                            ),
                        ],
                        EgaugeIoList=[]
                    )
                )
            ],
            "ElectricMeterComponents"
        )
        self.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=str(uuid.uuid4()),
                    Alias="a.m",
                    Role=Role.PowerMeter,
                    ActorClass=ActorClass.PowerMeter,
                    DisplayName="Power Meter",
                    ComponentId=self.component_id_by_alias("Dummy Electric Meter Component"),
                ),
                SpaceheatNodeGt(
                    ShNodeId=str(uuid.uuid4()),
                    Alias="a.elt1",
                    Role=Role.BoostElement,
                    ActorClass=ActorClass.NoActor,
                    DisplayName="Dummy Boost Element",
                    InPowerMetering=True,
                ),
            ]
        )

    def add_stub_scada(self):
        self.misc["MyAtomicTNodeGNode"] = {
            "GNodeId": str(uuid.uuid4()),
            "Alias": "dummy.atn.gnode",
            "DisplayName": "ATN GNode",
            "GNodeStatusValue": "Active",
            "PrimaryGNodeRoleAlias": "AtomicTNode"
        }
        self.misc["MyScadaGNode"] = {
            "GNodeId": str(uuid.uuid4()),
            "Alias": "dummy.scada.gnode",
            "DisplayName": "Dummy Scada",
            "GNodeStatusValue": "Active",
            "PrimaryGNodeRoleAlias": "Scada"
        }
        self.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=str(uuid.uuid4()),
                    Alias="a.s",
                    Role=Role.Scada,
                    ActorClass=ActorClass.Scada,
                    DisplayName="scada",
                ),
                SpaceheatNodeGt(
                    ShNodeId=str(uuid.uuid4()),
                    Alias="a.home",
                    Role=Role.HomeAlone,
                    ActorClass=ActorClass.HomeAlone,
                    DisplayName="HomeAlone",
                ),
            ]
        )

    def add_stubs(self):
        self.add_stub_power_meter()
        self.add_stub_scada()

    def dict(self) -> dict:
        d = dict(
            self.misc,
            **{
                list_name: [
                    entry.as_dict() for entry in entries
                ]
                for list_name, entries in self.lists.items()
            }
        )
        return d

    def write(self, path: str | Path) -> None:
        with Path(path).open("w") as f:
            f.write(json.dumps(self.dict(), sort_keys=True, indent=2))