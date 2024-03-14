"""Temporary package for assisting generation of hardware_layout.json files"""
import json
import subprocess
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import uuid

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import ElectricMeterCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import ChannelConfig
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from gwproto.type_helpers import CACS_BY_MAKE_MODEL

@dataclass
class StubConfig:
    add_stub_scada: bool = True
    add_stub_george_hack: bool = False
    george_hack_display_name: str = "George Hack: First automated control node"
    atn_gnode_alias: str = "dummy.atn.gnode",
    scada_gnode_alias: str = "dummy.scada.gnode",
    scada_display_name: str = "Dummy Scada"
    add_stub_power_meter: bool = True
    power_meter_cac_display_name: str = "Dummy Power Meter Cac"
    power_meter_component_display_name: str = "Dummy Power Meter Component"
    power_meter_node_display_name: str = "Dummy Power Meter"
    hp_pwr_display_name: str = "Dummy Boost Element"

class LayoutIDMap:
    cacs_by_make_model: dict[MakeModel, str]
    cacs_w_unknown_make_model_id_list: list[str]
    components_by_display_name: dict[str, str]
    nodes_by_name: dict[str, str]
    gnodes: dict[str, dict]

    def __init__(self, d: Optional[dict] = None):
        self.components_by_display_name = {}
        self.nodes_by_name = {}
        self.gnodes = {}
        if not d:
            return
        for k, v in d.items():
                if isinstance(v, dict) and "GNodeId" in v:
                    self.gnodes[k] = v
                if k == "ShNodes":
                        for node in v:
                            try:
                                self.add_node(
                                    node["ShNodeId"],
                                    node["Alias"],
                                )
                            except Exception as e:
                                raise Exception(
                                    f"ERROR in LayoutIDMap() for {k}:{node}. Error: {type(e)}, <{e}>"
                                )
                elif k.lower().endswith("cacs"):
                        for cac in v:
                            try:
                                model = MakeModel(cac["MakeModelGtEnumSymbol"])
                                self.add_cac(
                                    cac["ComponentAttributeClassId"],
                                    model,
                                )
                            except Exception as e:
                                raise Exception(
                                    f"ERROR in LayoutIDMap() for {k}:{cac}. Error: {type(e)}, <{e}>"
                                )

                elif k.lower().endswith("components"):
                        for component in v:
                            try:
                                self.add_component(
                                    component["ComponentId"],
                                    component["DisplayName"],
                                )
                            except Exception as e:
                                raise Exception(
                                    f"ERROR in LayoutIDMap() for {k}:{component}. Error: {type(e)}, <{e}>"
                                )

    def add_cac(self, id_: str, make_model_: MakeModel):
        if make_model_ == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.cacs_w_unknown_make_model_id_list.append(id_)
        else:
            if CACS_BY_MAKE_MODEL[make_model_] != id_:
                raise Exception(f"cac make model {make_model_} does not have id <{id_}>:\n"
                                "see from gwproto.type_helpers import CACS_BY_MAKE_MODEL")
            self.cacs_by_make_model[make_model_] = id_

    def add_component(self, id_: str, display_name: str):
        self.components_by_display_name[display_name] = id_

    def add_node(self, id_: str, name: str):
        self.nodes_by_name[name] = id_

    @classmethod
    def from_path(cls, path: Path) -> "LayoutIDMap":
        with path.open() as f:
            return LayoutIDMap(json.loads(f.read()))

    @classmethod
    def from_rclone(cls, rclone_name: str, upload_dir: Path) -> "LayoutIDMap":
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True)
        dest_path = upload_dir / f"{rclone_name}.uploaded.json"
        upload = [
            "rclone",
            "copyto",
            f"{rclone_name}:/home/pi/.config/gridworks/scada/hardware-layout.json",
            f"{dest_path}",
        ]
        print(f"Running upload command:\n\n{' '.join(upload)}\n")
        result = subprocess.run(upload, capture_output=True)
        if result.returncode != 0:
            print(f"Command output:\n[\n{result.stderr.decode('utf-8')}\n]")
            raise RuntimeError(
                f"ERROR. Command <{' '.join(upload)}> failed with returncode:{result.returncode}"
            )
        return cls.from_path(dest_path)

class LayoutDb:
    lists: dict[str, list[ComponentAttributeClassGt | ComponentGt | SpaceheatNodeGt]]
    cacs_by_make_model: dict[str, ComponentAttributeClassGt]
    components_by_id: dict[str, ComponentGt]
    nodes_by_id: dict[str, SpaceheatNodeGt]
    loaded: LayoutIDMap
    maps: LayoutIDMap
    misc: dict

    def __init__(
        self,
        existing_layout: Optional[LayoutIDMap] = None,
        cacs: Optional[list[ComponentAttributeClassGt]] = None,
        components: Optional[list[ComponentGt]] = None,
        nodes: Optional[list[SpaceheatNodeGt]] = None,
        add_stubs: bool = False,
        stub_config: Optional[StubConfig] = None,
    ):
        self.lists = dict(OtherComponents=[])
        self.cacs_by_id = {}
        self.components_by_make_model = {}
        self.nodes_by_id = {}
        self.misc = {}
        self.loaded = existing_layout or LayoutIDMap()
        self.maps = LayoutIDMap()
        if cacs is not None:
            self.add_cacs(cacs)
        if components is not None:
            self.add_components(components)
        if nodes is not None:
            self.add_nodes(nodes)
        if add_stubs:
            self.add_stubs(stub_config)

    def cac_id_by_make_model(self, make_model: MakeModel) -> Optional[str]:
        return self.maps.cacs_by_make_model.get(make_model, None)

    def component_id_by_display_name(self, component_display_name: str) -> Optional[str]:
        return self.maps.components_by_display_name.get(component_display_name, None)

    def node_id_by_name(self, node_name: str) -> Optional[str]:
        return self.maps.nodes_by_name.get(node_name, None)

    def make_component_id(self, component_display_name: str) -> str:
        return self.loaded.components_by_display_name.get(component_display_name, str(uuid.uuid4()))

    def make_node_id(self, node_name: str) -> str:
        return self.loaded.nodes_by_name.get(node_name, str(uuid.uuid4()))

    def add_cacs(self, cacs:list[ComponentAttributeClassGt], layout_list_name: str = "OtherCacs"):
        for cac in cacs:
            if cac.ComponentAttributeClassId in self.maps.cacs_w_unknown_make_model_id_list:
                raise ValueError(
                    f"ERROR: cac with id <{cac.ComponentAttributeClassId}> "
                    "already present"
                )
            elif cac.MakeModel in self.maps.cacs_by_make_model:
                raise ValueError(
                    f"ERROR: cac with MakeModel <{cac.MakeModel}> "
                    "already present"
                )
            self.cacs_by_id[cac.ComponentAttributeClassId] = cac
            self.maps.add_cac(
                cac.ComponentAttributeClassId,
                cac.MakeModel
            )
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
            if component.DisplayName in self.maps.components_by_display_name:
                raise ValueError(
                    f"ERROR. Component with DisplayName {component.DisplayName} "
                    "already present."
                )
            self.components_by_id[component.ComponentId] = component
            self.maps.add_component(
                component.ComponentId,
                component.DisplayName,
            )
            if layout_list_name not in self.lists:
                self.lists[layout_list_name] = []
            self.lists[layout_list_name].append(component)

    def add_nodes(self, nodes:list[SpaceheatNodeGt]):
        for node in nodes:
            if node.ShNodeId in self.nodes_by_id:
                raise ValueError(
                    f"ERROR Node id {node.ShNodeId} already present."
                )
            if node.Name in self.maps.nodes_by_name:
                raise ValueError(
                    f"ERROR Node alias {node.Name} already present."
                )
            self.nodes_by_id[node.ShNodeId] = node
            self.maps.add_node(node.ShNodeId, node.Name)
            layout_list_name = "ShNodes"
            if layout_list_name not in self.lists:
                self.lists[layout_list_name] = []
            self.lists[layout_list_name].append(node)

    def add_stub_power_meter(self, cfg: Optional[StubConfig] = None):
        if cfg is None:
            cfg = StubConfig()
        electric_meter_cac_type = "electric.meter.cac.gt"
        if not self.cac_id_by_make_model(MakeModel.GRIDWORKS__SIMPM1):
            self.add_cacs(
                [
                    typing.cast(
                        ComponentAttributeClassGt,
                        ElectricMeterCacGt(
                            ComponentAttributeClassId=CACS_BY_MAKE_MODEL[MakeModel.GRIDWORKS__SIMPM1],
                            MakeModel=MakeModel.GRIDWORKS__SIMPM1,
                            DisplayName=cfg.power_meter_cac_display_name,
                            TelemetryNameList=[TelemetryName.PowerW],
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
                        ComponentId=self.make_component_id(cfg.power_meter_component_display_name),
                        ComponentAttributeClassId=(electric_meter_cac_type),
                        DisplayName=cfg.power_meter_component_display_name,
                        ConfigList=[
                        ChannelConfig(
                            ChannelName="hp-idu-pwr",
                            PollPeriodMs=1000,
                            CapturePeriodS=60,
                            AsyncCapture=True,
                            AsyncCaptureDelta=20,
                            Exponent=1,
                            Unit=Unit.W,
                        )
                    ],
                        EgaugeIoList=[]
                    )
                )
            ],
            "ElectricMeterComponents"
        )
        power_meter_name = "power-meter"
        hp_pwr_name = "hp-pwr"
        self.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=self.make_node_id(power_meter_name),
                    Alias=power_meter_name,
                    ActorClass=ActorClass.PowerMeter,
                    DisplayName=cfg.power_meter_node_display_name,
                    ComponentId=self.component_id_by_display_name(cfg.power_meter_component_display_name),
                ),
                SpaceheatNodeGt(
                    ShNodeId=self.make_node_id(hp_pwr_name),
                    Name=hp_pwr_name,
                    ActorClass=ActorClass.NoActor,
                    DisplayName=cfg.hp_pwr_display_name,
                    InPowerMetering=True,
                ),
            ]
        )

    def add_stub_scada(self, cfg: Optional[StubConfig] = None):
        if cfg is None:
            cfg = StubConfig()
        if self.loaded.gnodes:
            self.misc.update(self.loaded.gnodes)
        else:
            self.misc["MyAtomicTNodeGNode"] = {
                "GNodeId": str(uuid.uuid4()),
                "Alias": cfg.atn_gnode_alias,
                "DisplayName": "ATN GNode",
                "GNodeStatusValue": "Active",
                "PrimaryGNodeRoleAlias": "AtomicTNode"
            }
            self.misc["MyScadaGNode"] = {
                "GNodeId": str(uuid.uuid4()),
                "Alias": cfg.scada_gnode_alias,
                "DisplayName": "Scada GNode",
                "GNodeStatusValue": "Active",
                "PrimaryGNodeRoleAlias": "Scada"
            }
            self.misc["MyTerminalAssetGNode"] = {
                "GNodeId": str(uuid.uuid4()),
                "Alias": "dummy.ta",
                "DisplayName": "Dummy TerminalAsset",
                "GNodeStatusValue": "Active",
                "PrimaryGNodeRoleAlias": "TerminalAsset"
              }

        scada_name="s"
        scada_handle="h.s"
        home_name="h"
        home_handle="h"
        self.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=self.make_node_id(scada_name),
                    Name=scada_name,
                    Handle=scada_handle,
                    ActorClass=ActorClass.Scada,
                    DisplayName=cfg.scada_display_name,
                ),
                SpaceheatNodeGt(
                    ShNodeId=self.make_node_id(home_name),
                    Name=home_name,
                    Handle=home_handle,
                    ActorClass=ActorClass.HomeAlone,
                    DisplayName="HomeAlone",
                ),
            ]
        )

    def add_stub_george_hack(self, cfg: Optional[StubConfig] = None):
        if cfg is None:
            cfg = StubConfig()
        george_hack_name = "gh"
        george_hack_handle = "gh"
        self.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=self.make_node_id(george_hack_name),
                    Name=george_hack_name,
                    Handle=george_hack_handle,
                    ActorClass=ActorClass.NoActor,
                    DisplayName=cfg.george_hack_display_name,
                ),
            ]
        )


    def add_stubs(self, cfg: Optional[StubConfig] = None):
        if cfg is None:
            cfg = StubConfig()
        if cfg.add_stub_power_meter:
            self.add_stub_power_meter(cfg)
        if cfg.add_stub_scada:
            self.add_stub_scada(cfg)
        if cfg.add_stub_george_hack:
            self.add_stub_george_hack()

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