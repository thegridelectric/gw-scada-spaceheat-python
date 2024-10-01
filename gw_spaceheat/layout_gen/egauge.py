from typing import cast
from typing import Optional

from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.enums import ActorClass
from gwproto.enums import LocalCommInterface
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName 
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import EgaugeRegisterConfig
from gwproto.types import ElectricMeterCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import ElectricMeterChannelConfig
from gwproto.types import DataChannelGt
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from pydantic import BaseModel

from data_classes.house_0 import H0N
from layout_gen.layout_db import LayoutDb


class ChannelMeterConfig(BaseModel):
    AboutNodeName: str
    EGaugeAddress: int
    EGuageName: str
    NameplatePowerW: int = 3500
    AsyncCaptureDelta: int = 250
    AsyncCapture: bool = True
    InPowerMetering: bool = False


    def node(self, db: LayoutDb) -> SpaceheatNodeGt:
        return SpaceheatNodeGt(
            ShNodeId=db.make_node_id(self.AboutNodeName),
            Alias=self.AboutNodeName,
            ActorClass=ActorClass.NoActor,
            Role=Role.Unknown,
            DisplayName=' '.join(word.capitalize() for word in self.AboutNodeName.split('-')),
            InPowerMetering=self.InPowerMetering,
            NameplatePowerW=self.NameplatePowerW
        )

    def channel_config(self, **kwargs) -> ElectricMeterChannelConfig:
        kwargs_used = dict(
            ChannelName=f"{self.AboutNodeName}-pwr",
            PollPeriodMs = 1000,
            CapturePeriodS=60,
            AsyncCapture=self.AsyncCapture,
            AsyncCaptureDelta=self.AsyncCaptureDelta,
            Exponent=0,
            Unit=Unit.W,
            EgaugeRegisterConfig=EgaugeRegisterConfig(
                                    Address=self.EGaugeAddress,
                                    Name=self.EGuageName,
                                    Description="change in value",
                                    Type="f32",
                                    Denominator=1,
                                    Unit=Unit.W
                )
        )
        kwargs_used.update(kwargs)
        return ElectricMeterChannelConfig(**kwargs_used)

#assumes for now it is an egauge
class PowerMeterGenConfig(BaseModel):
    NodeName: str = H0N.primary_power_meter
    NodeDisplayName: str = "Primary Power Meter"
    ComponentDisplayName: str = "EGauge Power Meter"
    HwUid: str
    ModbusHost: str
    ModbusPort: int = 502
    CapturePeriodS: int = 60
    PollPeriodMs: int = 1000
    ChannelConfigs: list[ChannelMeterConfig]

    def channel_configs(
        self,
        kwargs: Optional[dict] = None,
    ) -> list[ChannelMeterConfig]:
        if kwargs is None:
            kwargs = {}
        kwargs["CapturePeriodS"] = self.CapturePeriodS
        kwargs["PollPeriodMs"] = self.PollPeriodMs
        return [
            ch.channel_config(kwargs=kwargs)
            for ch in self.ChannelConfigs
        ]

def add_egauge(
    db: LayoutDb,
    egauge: PowerMeterGenConfig,
) -> None:
    make_model = MakeModel.EGAUGE__4030
    if not db.cac_id_by_alias(make_model):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    ElectricMeterCacGt(
                        ComponentAttributeClassId=CACS_BY_MAKE_MODEL[make_model],
                        MakeModel=make_model,
                        PollPeriodMs=1000,
                        DisplayName="EGauge 4030",
                        Interface=LocalCommInterface.ETHERNET,
                        TelemetryNameList=[TelemetryName.PowerW],
                    )
                )
            ],
            "ElectricMeterCacs",
        )
    db.add_components(
        [
            cast(
                ComponentGt,
                ElectricMeterComponentGt(
                    ComponentId=db.make_component_id(egauge.ComponentDisplayName),
                    ComponentAttributeClassId=db.cac_id_by_alias(make_model),
                    DisplayName=egauge.ComponentDisplayName,
                    ConfigList=egauge.channel_configs(),
                    HwUid=egauge.HwUid,
                    ModbusHost=egauge.ModbusHost,
                    ModbusPort=egauge.ModbusPort,
                )
            )
        ],
        "ElectricMeterComponents",
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(egauge.NodeName),
                Alias=egauge.NodeName,
                ActorClass=ActorClass.PowerMeter,
                Role=Role.PowerMeter,
                DisplayName=egauge.NodeDisplayName,
                ComponentId=db.component_id_by_alias(egauge.ComponentDisplayName),
            )
        ] + [io.node(db) for io in egauge.ChannelConfigs]
    )
    db.add_data_channels(
        [
            
        ]
    )
