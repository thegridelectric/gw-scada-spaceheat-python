from typing import cast

from typing import Optional

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import MultipurposeSensorCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import TelemetryReportingConfig
from gwproto.types.multipurpose_sensor_component_gt import MultipurposeSensorComponentGt
from pydantic import BaseModel

from layout_gen.layout_db import LayoutDb

class SensorNodeGenCfg(BaseModel):
    NodeAlias: str
    Role: Role
    DisplayName: str
    ReportOnChange: bool = True
    SamplePeriodS: int = 60
    ReportingSamplePeriodS: Optional[int] = None
    Exponent = 3
    # Using a forward reference here resolves a pydantic exception generated when this field
    # is actually set, as in tlayouts/gen_oak.py. I don't know why we should need a forward
    # reference, since TelemetryName is imported above. The generated error is:
    #
    # pydantic.errors.ConfigError: field "TelemetryName" not yet prepared so
    #   type is still a ForwardRef, you might need to call
    #   SensorNodeGenCfg.update_forward_refs().
    Unit: "Unit" = Unit.Celcius
    TelemetryName: "TelemetryName" = TelemetryName.WaterTempCTimes1000
    AsyncReportThreshold: Optional[float] = None
    NameplateMaxValue: Optional[int] = None

class TSnapMultipurposeGenCfg(BaseModel):
    NodeAlias: str
    InHomeName: str
    HWUid: str
    ChannelList: list[int]
    SensorCfgs: list[SensorNodeGenCfg]

    def node_display_name(self) -> str:
        return f"Multipurpose Temp Sensor <{self.InHomeName}>"

    def component_alias(self) -> str:
        return f"Multipurpose Temp Sensor Component <{self.HWUid}>"

def add_tsnap_multipurpose(
    db: LayoutDb,
    tsnap: TSnapMultipurposeGenCfg,
) -> None:
    cac_type = "multipurpose.sensor.cac.gt"
    if not db.cac_id_by_type(cac_type):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    MultipurposeSensorCacGt(
                        ComponentAttributeClassId=db.make_cac_id(cac_type),
                        MakeModel=MakeModel.GRIDWORKS__TSNAP1,
                        PollPeriodMs=200,
                        Exponent=0,
                        TempUnit=Unit.Celcius,
                        TelemetryNameList=[TelemetryName.WaterTempCTimes1000],
                        MaxThermistors=12,
                        DisplayName="GridWorks TSnap1.0 as 12-channel analog temp sensor",
                        CommsMethod="i2c",
                    )
                )
            ],
            "MultipurposeSensorCacs",
        )
    db.add_components(
        [
            cast(
                ComponentGt,
                MultipurposeSensorComponentGt(
                    ComponentId=db.make_component_id(tsnap.component_alias()),
                    ComponentAttributeClassId=db.cac_id_by_type(cac_type),
                    ChannelList=list(tsnap.ChannelList),
                    ConfigList=[
                        TelemetryReportingConfig(
                            AboutNodeName=sensor_cfg.NodeAlias,
                            ReportOnChange=sensor_cfg.ReportOnChange,
                            SamplePeriodS=sensor_cfg.SamplePeriodS,
                            Exponent=sensor_cfg.Exponent,
                            Unit=sensor_cfg.Unit,
                            TelemetryName=sensor_cfg.TelemetryName,
                            AsyncReportThreshold=sensor_cfg.AsyncReportThreshold,
                            NameplateMaxValue=sensor_cfg.NameplateMaxValue,
                        )
                        for sensor_cfg in tsnap.SensorCfgs
                    ],
                    DisplayName=tsnap.component_alias(),
                    HwUid=tsnap.HWUid
                )
            )
        ],
        "MultipurposeSensorComponents",
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tsnap.NodeAlias),
                Alias=tsnap.NodeAlias,
                ActorClass=ActorClass.MultipurposeSensor,
                Role=Role.MultiChannelAnalogTempSensor,
                DisplayName=tsnap.node_display_name(),
                ComponentId=db.component_id_by_alias(tsnap.component_alias())
            )
        ] + [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(sensor_cfg.NodeAlias),
                Alias=sensor_cfg.NodeAlias,
                ActorClass=ActorClass.NoActor,
                Role=sensor_cfg.Role,
                DisplayName=sensor_cfg.DisplayName,
                ReportingSamplePeriodS=sensor_cfg.ReportingSamplePeriodS,
            )
            for sensor_cfg in tsnap.SensorCfgs
        ]
    )
