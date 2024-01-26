from typing import cast
from typing import Optional

from pydantic import BaseModel

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import PipeFlowSensorCacGt
from gwproto.types import PipeFlowSensorComponentGt
from gwproto.types import SpaceheatNodeGt

from layout_gen.layout_db import LayoutDb

class FlowMeterGenCfg(BaseModel):
    NodeAlias: str
    I2cAddress: int
    ConversionFactor: float
    PollPeriodS: float = 5
    ReportingSamplePeriodS: Optional[int] = None

    def node_display_name(self) -> str:
        return f"Pipe Flow Meter <{self.NodeAlias}>"

    def component_alias(self) -> str:
        return f"Pipe Flow Meter Component <{self.NodeAlias}>"

class Istec4440FlowMeterGenCfg(FlowMeterGenCfg):
    ConversionFactor: float = 0.268132

class SmallOmegaFlowMeterGenCfg(FlowMeterGenCfg):
    # For the Omega FTB8007 series that give a tick every 0.1 gallons
    ConversionFactor: float = 0.134066


class LargeOmegaFlowMeterGenCfg(FlowMeterGenCfg):
    # For the Omega FTB8010 series that give a tick every gallon
    ConversionFactor: float = 1.34066


def add_flow_meter(
    db: LayoutDb,
    flow_meter: FlowMeterGenCfg,
) -> None:
    cac_type = "pipe.flow.sensor.cac.gt"
    if not db.cac_id_by_type(cac_type):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    PipeFlowSensorCacGt(
                        ComponentAttributeClassId=db.make_cac_id(cac_type),
                        MakeModel=MakeModel.ATLAS__EZFLO,
                        DisplayName="Atlas Scientific EZO FLO i2c",
                    )
                )
            ],
            "PipeFlowSensorCacs",
        )
    db.add_components(
        [
            cast(
                ComponentGt,
                PipeFlowSensorComponentGt(
                    ComponentId=db.make_component_id(flow_meter.component_alias()),
                    ComponentAttributeClassId=db.cac_id_by_type(cac_type),
                    I2cAddress=flow_meter.I2cAddress,
                    ConversionFactor=flow_meter.ConversionFactor,
                    DisplayName=flow_meter.component_alias(),
                    PollPeriodS=flow_meter.PollPeriodS
                )
            )
        ],
        "PipeFlowSensorComponents",
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(flow_meter.NodeAlias),
                Alias=flow_meter.NodeAlias,
                ActorClass=ActorClass.SimpleSensor,
                Role=Role.PipeFlowMeter,
                DisplayName=flow_meter.node_display_name(),
                ComponentId=db.component_id_by_alias(flow_meter.component_alias()),
                ReportingSamplePeriodS=flow_meter.ReportingSamplePeriodS,
            )
        ]
    )

def add_istec_flow_meter(
    db: LayoutDb,
    flow_meter: Istec4440FlowMeterGenCfg,
) -> None:
    return add_flow_meter(db, flow_meter)

