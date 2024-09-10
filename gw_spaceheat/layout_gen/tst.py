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
from gwproto.types import RelayCacGt
from gwproto.types import RelayComponentGt
from gwproto.types import ResistiveHeaterCacGt
from gwproto.types import ResistiveHeaterComponentGt
from gwproto.types import SimpleTempSensorCacGt
from gwproto.types import SimpleTempSensorComponentGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import TelemetryReportingConfig
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt

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
    _add_relay(db)
    _add_simple_sensor(db)
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

def _add_relay(db: LayoutDb) -> LayoutDb:
    RELAY_CAC_TYPE_NAME = "relay.cac.gt"
    RELAY_COMPONENT_DISPLAY_NAME = "Gridworks Simulated Boolean Actuator"
    RELAY_NODE_NAME = "a.elt1.relay"
    if not db.cac_id_by_type(RELAY_CAC_TYPE_NAME):
        db.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    RelayCacGt(
                        ComponentAttributeClassId=db.make_cac_id(RELAY_CAC_TYPE_NAME),
                        MakeModel=MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY,
                        DisplayName="Gridworks Simulated Boolean Actuator",
                        TypicalResponseTimeMs=400,
                    )
                ),
            ],
            "RelayCacs"
        )
    db.add_components(
        [
            typing.cast(
                ComponentGt,
                RelayComponentGt(
                    ComponentId=db.make_component_id(RELAY_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_type(RELAY_CAC_TYPE_NAME),
                    DisplayName=RELAY_COMPONENT_DISPLAY_NAME,
                    Gpio=0,
                    NormallyOpen=True,
                ),
            ),
        ],
        "RelayComponents"
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(RELAY_NODE_NAME),
                Alias=RELAY_NODE_NAME,
                Role=Role.BooleanActuator,
                ActorClass=ActorClass.BooleanActuator,
                DisplayName="30A Relay for first boost element",
                ComponentId=db.component_id_by_alias(RELAY_COMPONENT_DISPLAY_NAME),
            ),
        ]
    )
    return db

def _add_simple_sensor(db: LayoutDb) -> LayoutDb:
    SIMPLE_SENSOR_CAC_TYPE_NAME = "simple.temp.sensor.cac.gt"
    SIMPLE_SENSOR_COMPONENT_DISPLAY_NAME = "Component for a.tank.temp0 (on top)"
    SIMPLE_SENSOR_NODE_NAME = "a.tank.temp0"
    if not db.cac_id_by_type(SIMPLE_SENSOR_CAC_TYPE_NAME):
        db.add_cacs(
            [
                typing.cast(
                    ComponentAttributeClassGt,
                    SimpleTempSensorCacGt(
                        ComponentAttributeClassId=db.make_cac_id(SIMPLE_SENSOR_CAC_TYPE_NAME),
                        MakeModel=MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION,
                        DisplayName="Simulated GridWorks high precision water temp sensor",
                        CommsMethod="SassyMQ",
                        Exponent=-3,
                        TempUnit=Unit.Fahrenheit,
                        TelemetryName=TelemetryName.WaterTempFTimes1000,
                        TypicalResponseTimeMs=880,
                    )
                )
            ],
            "SimpleTempSensorCacs"
        )
    db.add_components(
        [
            typing.cast(
                ComponentGt,
                SimpleTempSensorComponentGt(
                    ComponentId=db.make_component_id(SIMPLE_SENSOR_COMPONENT_DISPLAY_NAME),
                    ComponentAttributeClassId=db.cac_id_by_type(SIMPLE_SENSOR_CAC_TYPE_NAME),
                    DisplayName=SIMPLE_SENSOR_COMPONENT_DISPLAY_NAME,
                    HwUid="1023abcd"
                ),
            ),
        ],
        "SimpleTempSensorComponents"
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(SIMPLE_SENSOR_NODE_NAME),
                Alias=SIMPLE_SENSOR_NODE_NAME,
                Role=Role.TankWaterTempSensor,
                ActorClass=ActorClass.SimpleSensor,
                DisplayName="Tank temp sensor temp0 (on top)",
                ComponentId=db.component_id_by_alias(SIMPLE_SENSOR_COMPONENT_DISPLAY_NAME),
                ReportingSamplePeriodS=5,
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
    POWER_METER_NODE_NAME = "a.m"
    RESISTIVE_HEATER_1_NODE_NAME = "a.elt1"
    RESISTIVE_HEATER_2_NODE_NAME = "a.elt2"

    if not db.cac_id_by_type(ELECTRIC_METER_CAC_TYPE_NAME):
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
    if not db.cac_id_by_type(RESISTIVE_HEATER_CAC_TYPE_NAME):
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
                    ComponentAttributeClassId=db.cac_id_by_type(ELECTRIC_METER_CAC_TYPE_NAME),
                    DisplayName=POWER_METER_COMPONENT_DISPLAY_NAME,
                    ConfigList=[
                        # CurrentRmsMicroAmps
                        # AmpsRms
                        TelemetryReportingConfig(
                            AboutNodeName="a.elt1",
                            ReportOnChange=True,
                            SamplePeriodS=300,
                            NameplateMaxValue=4500,
                            Exponent=0,
                            AsyncReportThreshold=0.02,
                            TelemetryName=TelemetryName.PowerW,
                            Unit=Unit.W,
                        ),
                        TelemetryReportingConfig(
                            AboutNodeName="a.elt1",
                            ReportOnChange=True,
                            SamplePeriodS=300,
                            NameplateMaxValue=18750000,
                            AsyncReportThreshold=0.02,
                            Exponent=6,
                            TelemetryName=TelemetryName.CurrentRmsMicroAmps,
                            Unit=Unit.AmpsRms,
                        ),
                        TelemetryReportingConfig(
                            AboutNodeName="a.elt2",
                            ReportOnChange=True,
                            SamplePeriodS=300,
                            NameplateMaxValue=4500,
                            AsyncReportThreshold=0.02,
                            Exponent=0,
                            TelemetryName=TelemetryName.PowerW,
                            Unit=Unit.W,
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
                    ComponentAttributeClassId=db.cac_id_by_type(RESISTIVE_HEATER_CAC_TYPE_NAME),
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
                    ComponentAttributeClassId=db.cac_id_by_type(RESISTIVE_HEATER_CAC_TYPE_NAME),
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
    return db


