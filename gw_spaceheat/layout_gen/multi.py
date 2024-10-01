from typing import cast

from typing import Optional

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName
from gwproto.enums import Unit
from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import Ads111xBasedCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import  ChannelConfig
from gwproto.types.ads111x_based_component_gt import Ads111xBasedComponentGt
from pydantic import BaseModel

from layout_gen.layout_db import LayoutDb

class SensorNodeGenCfg(BaseModel):
    ChannelName: str
    DisplayName: str
    Role: "Role" = Role.Unknown
    AsyncCapture: bool = True
    CapturePeriodS: int = 60
    Exponent: int = 3
    # Using a forward reference here resolves a pydantic exception generated when this field
    # is actually set, as in tlayouts/gen_oak.py. I don't know why we should need a forward
    # reference, since TelemetryName is imported above. The generated error is:
    #
    # pydantic.errors.ConfigError: field "TelemetryName" not yet prepared so
    #   type is still a ForwardRef, you might need to call
    #   SensorNodeGenCfg.update_forward_refs().
    Unit: "Unit" = Unit.Celcius
    TelemetryName: "TelemetryName" = TelemetryName.WaterTempCTimes1000
    AsyncCaptureDelta: Optional[int] = None


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
    make_model = MakeModel.GRIDWORKS__TSNAP1
    if not db.cac_id_by_alias(make_model):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    Ads111xBasedCacGt(
                        ComponentAttributeClassId=CACS_BY_MAKE_MODEL[make_model],
                        MakeModel=make_model,
                        AdsI2cAddressList= ["0x4b", "0x48", "0x49"],
                        TelemetryNameList=[TelemetryName.WaterTempCTimes1000, TelemetryName.AirTempCTimes1000],
                        TotalTerminalBlocks=12,
                        MinPollPeriodMs=200,
                        DisplayName="GridWorks TSnap1.0 as 12-channel analog temp sensor",
                        CommsMethod="i2c",
                    )
                )
            ],
            "Ads111xBasedCacs",
        )
    db.add_components(
        [
            cast(
                ComponentGt,
                Ads111xBasedComponentGt(
                    ComponentId=db.make_component_id(tsnap.component_alias()),
                    ComponentAttributeClassId=db.cac_id_by_alias(make_model),
                    ChannelList=list(tsnap.ChannelList),
                    ConfigList=[
                        ChannelConfig(
                            ChannelName=sensor_cfg.ChannelName,
                            AsyncCapture=sensor_cfg.AsyncCapture,
                            CapturePeriodS=sensor_cfg.CapturePeriodS,
                            Exponent=sensor_cfg.Exponent,
                            Unit=sensor_cfg.Unit,
                            AsyncCaptureDelta=sensor_cfg.AsyncCaptureDelta,
                        )
                        for sensor_cfg in tsnap.SensorCfgs
                    ],
                    DisplayName=tsnap.component_alias(),
                    HwUid=tsnap.HWUid
                )
            )
        ],
        "Ads111xBasedComponents",
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
                ShNodeId=db.make_node_id(sensor_cfg.ChannelName),
                Alias=sensor_cfg.ChannelName, # 
                ActorClass=ActorClass.NoActor,
                Role=sensor_cfg.Role,
                DisplayName=sensor_cfg.DisplayName,
            )
            for sensor_cfg in tsnap.SensorCfgs
        ]
    )
    db.add_data_channels()
