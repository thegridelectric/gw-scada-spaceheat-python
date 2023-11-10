from typing import cast

import uuid

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

from layout_gen import LayoutDb

class SensorNodeGenCfg(BaseModel):
    NodeAlias: str
    Role: Role
    DisplayName: str

class TSnapMultipurposeGenCfg(BaseModel):
    NodeAlias: str
    InHomeName: str
    HWUid: str
    ChannelList: list[int] = [1, 3, 5, 7]
    SensorCfgs: list[SensorNodeGenCfg]

    def node_display_name(self) -> str:
        return f"Multipurpose Temp Sensor <{self.InHomeName}>"

    def component_alias(self) -> str:
        return f"Multipurpose Temp Sensor Component <{self.HWUid}>"

def add_tsnap_multipurpose(
    db: LayoutDb,
    tsnap: TSnapMultipurposeGenCfg,
) -> None:
    if not db.cac_id_by_type("multipurpose.sensor.cac.gt"):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    MultipurposeSensorCacGt(
                        ComponentAttributeClassId=str(uuid.uuid4()),
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
                    ComponentId=str(uuid.uuid4()),
                    ComponentAttributeClassId=db.cac_id_by_type(
                        "multipurpose.sensor.cac.gt"
                    ),
                    ChannelList=list(tsnap.ChannelList),
                    ConfigList=[
                        TelemetryReportingConfig(
                            AboutNodeName=sensor_cfg.NodeAlias,
                            ReportOnChange=False,
                            SamplePeriodS=60,
                            Exponent=3,
                            Unit=Unit.Celcius,
                            TelemetryName=TelemetryName.WaterTempCTimes1000,

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
                ShNodeId=str(uuid.uuid4()),
                Alias=tsnap.NodeAlias,
                ActorClass=ActorClass.MultipurposeSensor,
                Role=Role.MultiChannelAnalogTempSensor,
                DisplayName=tsnap.node_display_name(),
                ComponentId=db.component_id_by_alias(tsnap.component_alias())
            )
        ] + [
            SpaceheatNodeGt(
                ShNodeId=str(uuid.uuid4()),
                Alias=sensor_cfg.NodeAlias,
                ActorClass=ActorClass.NoActor,
                Role=sensor_cfg.Role,
                DisplayName=sensor_cfg.DisplayName,
            )
            for sensor_cfg in tsnap.SensorCfgs
        ]
    )
