import uuid
from typing import cast

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


class iSTECHFlowMeterGenCfg(BaseModel):
    NodeAlias: str
    I2cAddress: int
    ConversionFactor: float = 0.332
    PollPeriodS: float = 5

    def node_display_name(self) -> str:
        return f"Pipe Flow Meter <{self.NodeAlias}>"

    def component_alias(self) -> str:
        return f"Pipe Flow Meter Component <{self.NodeAlias}>"

def add_istech_flow_meter(
    db: LayoutDb,
    meter: iSTECHFlowMeterGenCfg,
) -> None:
    if not db.cac_id_by_type("pipe.flow.sensor.cac.gt"):
        db.add_cacs(
            [
                cast(
                    ComponentAttributeClassGt,
                    PipeFlowSensorCacGt(
                        ComponentAttributeClassId=str(uuid.uuid4()),
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
                    ComponentId=str(uuid.uuid4()),
                    ComponentAttributeClassId=db.cac_id_by_type(
                        "pipe.flow.sensor.cac.gt"
                    ),
                    I2cAddress=meter.I2cAddress,
                    ConversionFactor=meter.ConversionFactor,
                    DisplayName=meter.component_alias(),
                    PollPeriodS=meter.PollPeriodS
                )
            )
        ],
        "PipeFlowSensorComponents",
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=str(uuid.uuid4()),
                Alias=meter.NodeAlias,
                ActorClass=ActorClass.SimpleSensor,
                Role=Role.PipeFlowMeter,
                DisplayName=meter.node_display_name(),
                ComponentId=db.component_id_by_alias(meter.component_alias()),
                ReportingSamplePeriodS=30,
            )
        ]
    )
