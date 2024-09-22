from typing import cast
from typing import Optional

from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.enums import ActorClass
from gwproto.enums import LocalCommInterface
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.enums import TelemetryName as TelemetryNameEnum
from gwproto.enums import Unit as UnitEnum
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import EgaugeIo
from gwproto.types import EgaugeRegisterConfig
from gwproto.types import ElectricMeterCacGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types import TelemetryReportingConfig
from gwproto.types.electric_meter_component_gt import ElectricMeterComponentGt
from pydantic import BaseModel

from data_classes.house_0 import H0N
from layout_gen.layout_db import LayoutDb

class EGaugeIOGenCfg(BaseModel):
    AboutNodeName: str
    NodeRole: Role
    NodeDisplayName: str
    EGaugeAddress: int
    EGuageName: str
    NameplateMaxValue: int = 3500
    AsyncReportThreshold: float = 0.02
    InPowerMetering: bool = False

    def output_config(self, **kwargs) -> TelemetryReportingConfig:
        kwargs_used = dict(
            TelemetryName=TelemetryNameEnum.PowerW,
            AboutNodeName=self.AboutNodeName,
            ReportOnChange=True,
            SamplePeriodS=300,
            Exponent=0,
            Unit=UnitEnum.W,
            NameplateMaxValue=self.NameplateMaxValue,
            AsyncReportThreshold=self.AsyncReportThreshold,
        )
        kwargs_used.update(kwargs)
        return TelemetryReportingConfig(**kwargs_used)

    def egauge_register_config(self, **kwargs) -> EgaugeRegisterConfig:
        kwargs_used = dict(
            Address=self.EGaugeAddress,
            Name=self.EGuageName,
            Description="change in value",
            Type="f32",
            Denominator=1,
            Unit="W",
        )
        kwargs_used.update(kwargs)
        return EgaugeRegisterConfig(**kwargs_used)

    def node(self, db: LayoutDb) -> SpaceheatNodeGt:
        return SpaceheatNodeGt(
            ShNodeId=db.make_node_id(self.AboutNodeName),
            Alias=self.AboutNodeName,
            ActorClass=ActorClass.NoActor,
            Role=self.NodeRole,
            DisplayName=self.NodeDisplayName,
            InPowerMetering=self.InPowerMetering,
        )

    def egauge_io(
        self,
        egauge_kwargs: Optional[dict] = None,
        output_kwargs: Optional[dict] = None,
    ) -> EgaugeIo:
        if egauge_kwargs is None:
            egauge_kwargs = {}
        if output_kwargs is None:
            output_kwargs = {}
        return EgaugeIo(
            InputConfig=self.egauge_register_config(**egauge_kwargs),
            OutputConfig=self.output_config(**output_kwargs)
        )

class EGaugeGenCfg(BaseModel):
    NodeName: str = H0N.primary_power_meter
    NodeDisplayName: str = "Primary Power Meter"
    ComponentDisplayName: str = "EGauge Power Meter"
    HwUid: str
    ModbusHost: str
    ModbusPort: int = 502
    IOs: list[EGaugeIOGenCfg]

    def egauge_ios(
        self,
        egauge_kwargs: Optional[dict] = None,
        output_kwargs: Optional[dict] = None,
    ) -> list[EgaugeIo]:
        if egauge_kwargs is None:
            egauge_kwargs = {}
        if output_kwargs is None:
            output_kwargs = {}
        return [
            io.egauge_io(egauge_kwargs=egauge_kwargs, output_kwargs=output_kwargs)
            for io in self.IOs
        ]

    def config_list(self, **kwargs):
        return [io.output_config(**kwargs) for io in self.IOs]

def add_egauge(
    db: LayoutDb,
    egauge: EGaugeGenCfg,
) -> None:
    make_model = MakeModel.EGAUGE__4030
    if not db.cac_id_by_make_model(make_model):
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
                        TelemetryNameList=[TelemetryNameEnum.PowerW],
                    )
                )
            ],
            "ElectricMeterCacs",
        )
    io_list = egauge.egauge_ios()
    db.add_components(
        [
            cast(
                ComponentGt,
                ElectricMeterComponentGt(
                    ComponentId=db.make_component_id(egauge.ComponentDisplayName),
                    ComponentAttributeClassId=db.cac_id_by_make_model(make_model),
                    DisplayName=egauge.ComponentDisplayName,
                    ConfigList=[io.OutputConfig for io in io_list],
                    HwUid=egauge.HwUid,
                    ModbusHost=egauge.ModbusHost,
                    ModbusPort=egauge.ModbusPort,
                    EgaugeIoList=io_list,
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
        ] + [io.node(db) for io in egauge.IOs]
    )
