import typing
from pathlib import Path

from gwproto.enums import ActorClass
from gwproto.enums import LocalCommInterface
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import ElectricMeterCacGt
from gwproto.types import ResistiveHeaterCacGt
from gwproto.types import ResistiveHeaterComponentGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import ChannelConfig
from gwproto.types import DataChannelGt
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from data_classes.house_0 import H0N
from layout_gen import LayoutDb
from layout_gen import LayoutIDMap
from layout_gen import StubConfig


def make_tst_layout(src_path: Path) -> LayoutDb:
    db = LayoutDb(
        existing_layout=LayoutIDMap.from_path(src_path),
        add_stubs=True,
        stub_config=StubConfig(
            atn_gnode_alias="d1.isone.ct.newhaven.orange1",
            scada_gnode_alias="d1.isone.ct.newhaven.orange1.scada",
            scada_display_name="Little Orange House Main Scada",
            add_stub_power_meter=False,
        )
    )
    _add_power_meter(db)
    _add_atn(db)
    return db

def _add_atn(db: LayoutDb) -> LayoutDb:
    ATN_NODE_NAME = "a"
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
    ELECTRIC_METER_CAC_TYPE_NAME = "electric.meter.cac.gt"
    RESISTIVE_HEATER_CAC_TYPE_NAME = "resistive.heater.cac.gt"
    POWER_METER_COMPONENT_DISPLAY_NAME = "Power Meter for Simulated Test system"
    RESISTIVE_HEATER_1_COMPONENT_DISPLAY_NAME = "First 4.5 kW boost in tank"
    RESISTIVE_HEATER_2_COMPONENT_DISPLAY_NAME = "Second 4.5 kW boost in tank"
    POWER_METER_NODE_NAME = H0N.primary_power_meter
    RESISTIVE_HEATER_1_NODE_NAME = "elt1"
    RESISTIVE_HEATER_2_NODE_NAME = "elt2"

    if not db.cac_id_by_make_model(ELECTRIC_METER_CAC_TYPE_NAME):
        db.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    ElectricMeterCacGt(
                        ComponentAttributeClassId=db.make_cac_id(ELECTRIC_METER_CAC_TYPE_NAME),
                        MakeModel=MakeModel.GRIDWORKS__SIMPM1,
                        DisplayName="Gridworks Pm1 Simulated Power Meter",
                        TelemetryNameList=[TelemetryName.PowerW],
                        Interface=LocalCommInterface.SIMRABBIT,
                        PollPeriodMs=1000,
                    )
                ),
            ],
            "ElectricMeterCacs"
        )
    if not db.cac_id_by_make_model(RESISTIVE_HEATER_CAC_TYPE_NAME):
        db.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    ResistiveHeaterCacGt(
                        ComponentAttributeClassId=db.make_cac_id(RESISTIVE_HEATER_CAC_TYPE_NAME),
                        MakeModel=MakeModel.UNKNOWNMAKE__UNKNOWNMODEL,
                        DisplayName="Fake Boost Element",
                        NameplateMaxPowerW=4500,
                        RatedVoltageV=240,
                    )
                ),
            ],
            "ResistiveHeaterCacs"
        )

    db.add_components(
        [
            typing.cast(
                ComponentGt,
                ElectricMeterComponentGt(
                    ComponentId=db.make_component_id(POWER_METER_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_make_model(ELECTRIC_METER_CAC_TYPE_NAME),
                    DisplayName=POWER_METER_COMPONENT_DISPLAY_NAME,
                    ConfigList=[
                        # CurrentRmsMicroAmps
                        # AmpsRms
                        ChannelConfig(
                                ChannelName="elt1-pwr",
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptoreDelta=200,
                                Exponent=0
                            ),
                        ChannelConfig(
                                ChannelName="elt1-current",
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptoreDelta=1000,
                                Exponent=0
                            ), 
                        ChannelConfig(
                                ChannelName="elt2-pwr",
                                PollPeriodMs=1000,
                                CapturePeriodS=300,
                                AsyncCapture=True,
                                AsyncCaptoreDelta=200,
                                Exponent=0
                            ),
                    ],
                    EgaugeIoList=[]
                )
            ),
        ],
        "ElectricMeterComponents"
    )
    db.add_components(
        [
            typing.cast(
                ComponentGt,
                ResistiveHeaterComponentGt(
                    ComponentId=db.make_component_id(RESISTIVE_HEATER_1_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_make_model(RESISTIVE_HEATER_CAC_TYPE_NAME),
                    DisplayName=RESISTIVE_HEATER_1_COMPONENT_DISPLAY_NAME,
                    HwUid="aaaa2222",
                    TestedMaxColdMilliOhms=14500,
                    TestedMaxHotMilliOhms=13714,
                )
            ),
            typing.cast(
                ComponentGt,
                ResistiveHeaterComponentGt(
                    ComponentId=db.make_component_id(RESISTIVE_HEATER_2_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_make_model(RESISTIVE_HEATER_CAC_TYPE_NAME),
                    DisplayName=RESISTIVE_HEATER_2_COMPONENT_DISPLAY_NAME,
                    HwUid="bbbb2222",
                )
            ),
        ],
        "ResistiveHeaterComponents"
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(POWER_METER_NODE_NAME),
                Alias=POWER_METER_NODE_NAME,
                Role=Role.PowerMeter,
                ActorClass=ActorClass.PowerMeter,
                DisplayName="Main Power Meter Little Orange House Test System",
                ComponentId=db.component_id_by_alias(POWER_METER_COMPONENT_DISPLAY_NAME),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(RESISTIVE_HEATER_1_NODE_NAME),
                Alias=RESISTIVE_HEATER_1_NODE_NAME,
                Role=Role.BoostElement,
                ActorClass=ActorClass.NoActor,
                DisplayName="First 4.5 kW boost in tank",
                InPowerMetering=True,
                ComponentId=db.component_id_by_alias(RESISTIVE_HEATER_1_COMPONENT_DISPLAY_NAME),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(RESISTIVE_HEATER_2_NODE_NAME),
                Alias=RESISTIVE_HEATER_2_NODE_NAME,
                Role=Role.BoostElement,
                ActorClass=ActorClass.NoActor,
                DisplayName="Second boost element",
                InPowerMetering=True,
                ComponentId=db.component_id_by_alias(RESISTIVE_HEATER_2_COMPONENT_DISPLAY_NAME),
            ),
        ]
    )
    db.add_data_channels(
        [DataChannelGt(
            Name="elt1-pwr",
            AbotNodeName="elt1",
            CapturedByNodeName=H0N.primary_power_meter,
            TelemetryName=TelemetryName.PowerW,
            InPowerMetering=True,
            Id=db.make_channel_id("elt1-pwr"),
            TerminalAssetAlias=db.terminal_asset_alias,
        ),
        DataChannelGt(
            Name="elt1-current",
            AbotNodeName="elt1",
            CapturedByNodeName=H0N.primary_power_meter,
            TelemetryName=TelemetryName.CurrentRmsMicroAmps,
            InPowerMetering=True,
            Id=db.make_channel_id("elt1-current"),
            TerminalAssetAlias=db.terminal_asset_alias,
        ),
        DataChannelGt(
            Name="elt2-pwr",
            AbotNodeName="elt2",
            CapturedByNodeName=H0N.primary_power_meter,
            TelemetryName=TelemetryName.PowerW,
            InPowerMetering=True,
            Id=db.make_channel_id("elt2-pwr"),
            TerminalAssetAlias=db.terminal_asset_alias,
        )
        
        ]
    )
    return db


