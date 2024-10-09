from typing import Any, Dict, List, cast

from gwproto.enums import (
    ActorClass,
    FsmEventType,
    MakeModel,
    RelayWiringConfig,
    TelemetryName,
    Unit,
)
from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.types import (
    ChannelConfig,
    ComponentAttributeClassGt,
    ComponentGt,
    DataChannelGt,
    RelayActorConfig,
    SpaceheatNodeGt,
)
from gwproto.types.i2c_multichannel_dt_relay_component_gt import (
    I2cMultichannelDtRelayComponentGt,
)
from pydantic import BaseModel
from layout_gen.house_0 import SCADA_2_PARENT_NAME
from layout_gen.layout_db import LayoutDb



class I2cRelayPinCfg(BaseModel):
    RelayIdx: int
    DisplayName: str
    WiringConfig: RelayWiringConfig
    EventType: FsmEventType
    DeEnergizingEvent: Any
    PollPeriodMs: int = 5000
    CapturePeriodS: int = 300
    Boss: str = "h.admin"


class I2cRelayBoardCfg(BaseModel):
    NodeShortName: str
    NodeDisplayName: str = "Krida Board Multiplexer"
    ComponentDisplayName: str = "GSCADA double 16-pin Krida I2c Relay boards"
    I2cAddressList: List[int] = [0x20, 0x21]
    RelayMakeModel: MakeModel = MakeModel.KRIDA__DOUBLEEMR16I2CV3
    PinCfgByNameSuffix: Dict[str, I2cRelayPinCfg]
    Parent: str = SCADA_2_PARENT_NAME


def add_i2c_relay_board(
    db: LayoutDb,
    board: I2cRelayBoardCfg,
) -> None:
    if board.RelayMakeModel not in [
        MakeModel.KRIDA__DOUBLEEMR16I2CV3,
        MakeModel.KRIDA__EMR16I2CV3,
        MakeModel.GRIDWORKS__SIMDOUBLE16PINI2CRELAY,
    ]:
        raise Exception(
            f"make_model {board.RelayMakeModel} is not a I2cMultichannelDtRelayComponentGt MakeModel"
        )
    if board.RelayMakeModel == MakeModel.KRIDA__EMR16I2CV3:
        raise Exception(f"{MakeModel.KRIDA__EMR16I2CV3.value} not implemented yet!!")
    db.add_cacs(
        [
            ComponentAttributeClassGt(
                ComponentAttributeClassId=CACS_BY_MAKE_MODEL[board.RelayMakeModel],
                MakeModel=board.RelayMakeModel,
                DisplayName=board.ComponentDisplayName,
                MinPollPeriodMs=200,
            )
        ],
        "OtherCacs",
    )

    db.add_components(
        [
            cast(
                ComponentGt,
                I2cMultichannelDtRelayComponentGt(
                    ComponentId=db.make_component_id(board.ComponentDisplayName),
                    ComponentAttributeClassId=CACS_BY_MAKE_MODEL[board.RelayMakeModel],
                    I2cAddressList=[0x20, 0x21],
                    ConfigList=[
                        ChannelConfig(
                            ChannelName=f"{v}-energization",
                            PollPeriodMs=board.PinCfgByNameSuffix[v].PollPeriodMs,
                            CapturePeriodS=board.PinCfgByNameSuffix[v].CapturePeriodS,
                            AsyncCapture=True,
                            AsyncCaptureDelta=1,
                            Exponent=0,
                            Unit=Unit.Unitless,
                        )
                        for v in board.PinCfgByNameSuffix
                    ],
                    RelayConfigList=[
                        RelayActorConfig(
                            RelayIdx=board.PinCfgByNameSuffix[v].RelayIdx,
                            ActorName=f"{board.Parent}.{v}",
                            WiringConfig=board.PinCfgByNameSuffix[v].WiringConfig,
                            EventType=board.PinCfgByNameSuffix[v].EventType,
                            DeEnergizingEvent=board.PinCfgByNameSuffix[
                                v
                            ].DeEnergizingEvent,
                        )
                        for v in board.PinCfgByNameSuffix
                    ],
                    DisplayName=f"{board.ComponentDisplayName}, as component",
                ),
            )
        ],
        "I2cMultichannelDtRelayComponents",
    )

    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(f"{SCADA_2_PARENT_NAME}.{board.NodeShortName}"),
                Name=f"{SCADA_2_PARENT_NAME}.{board.NodeShortName}",
                Handle=f"{board.NodeShortName}",
                ActorClass=ActorClass.I2cRelayMultiplexer,
                DisplayName=board.NodeDisplayName,
                ComponentId=db.component_id_by_display_name(
                    f"{board.ComponentDisplayName}, as component"
                ),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(f"{SCADA_2_PARENT_NAME}.admin"),
                Name=f"{SCADA_2_PARENT_NAME}.admin",
                Handle="h.admin",
                ActorClass=ActorClass.Admin,
                DisplayName="Admin GNode",
            ),
        ]
        + [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(f"{board.Parent}.{k}"),
                Name=f"{board.Parent}.{k}",
                Handle=f"{board.PinCfgByNameSuffix[k].Boss}.{k}",
                ActorClass=ActorClass.Relay,
                DisplayName=board.PinCfgByNameSuffix[k].DisplayName,
                ComponentId=db.component_id_by_display_name(
                    f"{board.ComponentDisplayName}, as component"
                ),
            )
            for k in board.PinCfgByNameSuffix
        ]
    )

    db.add_channels(
        [
            DataChannelGt(
                Name=f"{k}-energization",
                DisplayName=f"{v.DisplayName}",
                AboutNodeName=f"{board.Parent}.{k}",
                CapturedByNodeName=f"{SCADA_2_PARENT_NAME}.{board.NodeShortName}",
                TelemetryName=TelemetryName.RelayState,
                Id=db.make_channel_id(f"{k}-energization"),
            )
            for k, v in board.PinCfgByNameSuffix.items()
        ]
    )
