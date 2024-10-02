import typing
from pathlib import Path

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import ElectricMeterCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import ElectricMeterChannelConfig
from gwproto.types import DataChannelGt
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from data_classes.house_0 import H0N, H0CN,ChannelStubByName
from layout_gen import LayoutDb
from layout_gen import LayoutIDMap
from layout_gen import StubConfig


def make_tst_layout(src_path: Path) -> LayoutDb:
    db = LayoutDb(
        existing_layout=LayoutIDMap.from_path(src_path),
        add_stubs=True,
        stub_config=StubConfig(
            atn_gnode_alias="d1.isone.ct.newhaven.orange1",
            scada_display_name="Little Orange House Main Scada",
            add_stub_power_meter=False,
        )
    )
    _add_power_meter(db)
    _add_atn(db)
    return db

def _add_atn(db: LayoutDb) -> LayoutDb:
    ATN_NODE_NAME = H0N.atn
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(ATN_NODE_NAME),
                Alias=ATN_NODE_NAME,
                Role=Role.Atn,
                ActorClass=ActorClass.Atn,
                DisplayName="AtomicTNode",
            ),
        ]
    )
    return db

def _add_power_meter(db: LayoutDb) -> LayoutDb:
    POWER_METER_COMPONENT_DISPLAY_NAME = "Power Meter for Simulated Test system"


    if not db.cac_id_by_alias(MakeModel.GRIDWORKS__SIMPM1):
        db.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    ElectricMeterCacGt(
                        ComponentAttributeClassId=db.make_cac_id(MakeModel.GRIDWORKS__SIMPM1),
                        MakeModel=MakeModel.GRIDWORKS__SIMPM1,
                        DisplayName="Gridworks Pm1 Simulated Power Meter",
                        TelemetryNameList=[TelemetryName.PowerW],
                        MinPollPeriodMs=1000,
                    )
                ),
            ],
            "ElectricMeterCacs"
        )

    db.add_components(
        [
            typing.cast(
                ComponentGt,
                ElectricMeterComponentGt(
                    ComponentId=db.make_component_id(POWER_METER_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_alias(MakeModel.GRIDWORKS__SIMPM1),
                    DisplayName=POWER_METER_COMPONENT_DISPLAY_NAME,
                    ConfigList=[
                        ElectricMeterChannelConfig(
                                ChannelName=H0CN.hp_odu_pwr,
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptureDelta=200,
                                Exponent=0,
                                Unit=Unit.W,
                            ),
                        ElectricMeterChannelConfig(
                                ChannelName=H0CN.hp_idu_pwr,
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptureDelta=200,
                                Exponent=0,
                                Unit=Unit.W,
                            ),
                        ElectricMeterChannelConfig(
                                ChannelName=H0CN.store_pump_pwr,
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptureDelta=5,
                                Exponent=0,
                                Unit=Unit.W,
                            )
                    ],
                )
            ),
        ],
        "ElectricMeterComponents"
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(H0N.primary_power_meter),
                Alias=H0N.primary_power_meter,
                Role=Role.PowerMeter,
                ActorClass=ActorClass.PowerMeter,
                DisplayName="Main Power Meter Little Orange House Test System",
                ComponentId=db.component_id_by_alias(POWER_METER_COMPONENT_DISPLAY_NAME),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(H0N.hp_odu),
                Alias=H0N.hp_odu,
                Role=Role.Unknown,
                ActorClass=ActorClass.NoActor,
                DisplayName="HP ODU",
                NameplatePowerW=6000,
                InPowerMetering=True,
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(H0N.hp_idu),
                Alias=H0N.hp_idu,
                Role=Role.Unknown,
                ActorClass=ActorClass.NoActor,
                DisplayName="HP IDU",
                NameplatePowerW=4000,
                InPowerMetering=True,
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(H0N.store_pump),
                Alias=H0N.store_pump,
                Role=Role.Unknown,
                ActorClass=ActorClass.NoActor,
                DisplayName="Store Pump",
            ),

        ]
    )
    db.add_data_channels(
        [
            DataChannelGt(
                Name=stub.Name,
                DisplayName=' '.join(part.upper() for part in stub.Name.split('-')),
                AboutNodeName=stub.AboutNodeName,
                CapturedByNodeName=stub.CapturedByNodeName,
                TelemetryName=stub.TelemetryName,
                InPowerMetering=stub.InPowerMetering,
                Id=db.make_channel_id(stub.Name),
                TerminalAssetAlias=db.terminal_asset_alias,
            )
            for stub in ChannelStubByName.values()
        ]
    )
    return db


