from typing import cast
from typing import Optional

from pydantic import BaseModel

from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Unit
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import ComponentGt
from gwproto.types import ChannelConfig
from gwproto.types.i2c_flow_totalizer_component_gt import I2cFlowTotalizerComponentGt

from gwproto.types import SpaceheatNodeGt
from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.type_helpers import CONVERSION_FACTOR_BY_MODEL

from layout_gen.layout_db import LayoutDb

class FlowMeterGenCfg(BaseModel):
    NodeName: str
    I2cAddress: int
    PulseFlowMeterMakeModel: MakeModel
    PollPeriodMs: float = 5000

    def node_display_name(self) -> str:
        return f"EZ FLo <{self.NodeName} ({self.PulseFlowMeterMakeModel.value}, I2c {self.I2cAddress})>"

    def component_display_name(self) -> str:
        return f"Component for EZ Flo ({self.PulseFlowMeterMakeModel.value}, I2c {self.I2cAddress})>"


def add_flow_meter(
    db: LayoutDb,
    i2c_totalizer: FlowMeterGenCfg,
) -> None:
    if not db.cac_id_by_make_model(MakeModel.ATLAS__EZFLO):
        db.add_cacs(
            [
                    ComponentAttributeClassGt(
                        ComponentAttributeClassId=CACS_BY_MAKE_MODEL[MakeModel.ATLAS__EZFLO],
                        MakeModel=MakeModel.ATLAS__EZFLO,
                        DisplayName="Atlas Scientific EZO FLO i2c",
                    )
                
            ],
            "OtherCacs",
        )
    db.add_components(
        [
            cast(
                ComponentGt,
                I2cFlowTotalizerComponentGt(
                    ComponentId=db.make_component_id(i2c_totalizer.component_display_name()),
                    ComponentAttributeClassId=CACS_BY_MAKE_MODEL[MakeModel.ATLAS__EZFLO],
                    I2cAddress=i2c_totalizer.I2cAddress,
                    ConfigList=[
                        ChannelConfig(
                            ChannelName=f"{i2c_totalizer.NodeName}-integrated",
                            PollPeriodMs=300,
                            CapturePeriodS=30,
                            AsyncCapture=True,
                            AsyncCaptureDelta=5,
                            Exponent=2,
                            Unit=Unit.Gallons,
                        ),
                        ChannelConfig(
                            ChannelName=i2c_totalizer.NodeName,
                            PollPeriodMs=300,
                            CapturePeriodS=30,
                            AsyncCapture=True,
                            AsyncCaptureDelta=20,
                            Exponent=2,
                            Unit=Unit.Gpm,
                        ),
                    ],
                    PulseFlowMeterMakeModel=i2c_totalizer.PulseFlowMeterMakeModel,
                    ConversionFactor=CONVERSION_FACTOR_BY_MODEL[i2c_totalizer.PulseFlowMeterMakeModel],
                    DisplayName=i2c_totalizer.component_display_name(),

                )
            )
        ],
        "I2cFlowTotalizerComponents",
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(i2c_totalizer.NodeName),
                Name=i2c_totalizer.NodeName,
                ActorClass=ActorClass.FlowTotalizer,
                DisplayName=i2c_totalizer.node_display_name(),
                ComponentId=db.component_id_by_display_name(i2c_totalizer.component_display_name()),
            )
        ]
    )



