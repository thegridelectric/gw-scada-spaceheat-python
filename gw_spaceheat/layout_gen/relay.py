from typing import List
from gwproto.enums import ActorClass, MakeModel, Unit, RelayWiringConfig, TelemetryName, FsmEventType, ChangeRelayState, ChangeAquastatControl, ChangeHeatcallSource, ChangeHeatPumpControl, ChangePrimaryPumpControl, ChangeStoreFlowDirection
from gwproto.named_types import I2cMultichannelDtRelayComponentGt
from pydantic import BaseModel
from gwproto.named_types.component_attribute_class_gt import ComponentAttributeClassGt
from gwproto.named_types import RelayActorConfig
from gwproto.data_classes.house_0_names import H0N, H0CN, House0RelayIdx
from gwproto.named_types import SpaceheatNodeGt, DataChannelGt
from layout_gen import LayoutDb
component_display_name = "i2c krida relay boards"

class RelayCfg(BaseModel):
    PollPeriodMs: int = 200
    CapturePeriodS: int = 300
    I2cAddressList: List[int] = [0x20, 0x21]

def add_relays(
        db: LayoutDb,
        cfg: RelayCfg,
    ) -> None:
    if not db.cac_id_by_alias(MakeModel.KRIDA__DOUBLEEMR16I2CV3):
        db.add_cacs(
            [
                ComponentAttributeClassGt(
                    ComponentAttributeClassId=db.make_cac_id(MakeModel.KRIDA__DOUBLEEMR16I2CV3),
                    DisplayName="16-channel i2c krida relay",
                    MakeModel=MakeModel.KRIDA__DOUBLEEMR16I2CV3,
                ),
            ]
        )
    House0RelayIdx.store_charge_disharge
    if not db.component_id_by_alias(component_display_name):
        config_list = [
                RelayActorConfig(
                    ChannelName=H0CN.vdc_relay_state,
                    RelayIdx=House0RelayIdx.vdc,
                    ActorName=H0N.vdc_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyClosed,
                    EventType=FsmEventType.ChangeRelayState,
                    DeEnergizingEvent=ChangeRelayState.CloseRelay,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless,
                ),
                RelayActorConfig(
                    ChannelName=H0CN.tstat_common_relay_state,
                    RelayIdx=House0RelayIdx.tstat_common,
                    ActorName=H0N.tstat_common_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyClosed,
                    EventType=FsmEventType.ChangeRelayState,
                    DeEnergizingEvent=ChangeRelayState.CloseRelay,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless,
                ),
                RelayActorConfig(
                    ChannelName=H0CN.charge_discharge_relay_state,
                    RelayIdx=House0RelayIdx.store_charge_disharge,
                    ActorName=H0N.store_charge_discharge_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyOpen,
                    EventType=FsmEventType.ChangeStoreFlowDirection,
                    DeEnergizingEvent=ChangeStoreFlowDirection.Discharge,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
        ]

        db.add_components(
            [
                I2cMultichannelDtRelayComponentGt(
                    ComponentId=db.make_component_id(component_display_name),
                    ComponentAttributeClassId=db.cac_id_by_alias(MakeModel.KRIDA__DOUBLEEMR16I2CV3),
                    DisplayName=component_display_name,
                    ConfigList=config_list,
                    I2cAddressList=cfg.I2cAddressList,
                )
            ]
        )

        db.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.relay_multiplexer),
                    Name=H0N.relay_multiplexer,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.relay_multiplexer}",
                    ActorClass=ActorClass.I2cRelayMultiplexer,
                    DisplayName="I2c Relay Multiplexer",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.vdc_relay),
                    Name=H0N.vdc_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.vdc_relay}",
                    Handle=f"{H0N.home_alone}.{H0N.vdc_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="5VDC Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.tstat_common_relay),
                    Name=H0N.tstat_common_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.tstat_common_relay}",
                    Handle=f"{H0N.home_alone}.{H0N.tstat_common_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="TStat Common Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.store_charge_discharge_relay),
                    Name=H0N.store_charge_discharge_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.store_charge_discharge_relay}",
                    Handle=f"{H0N.home_alone}.{H0N.store_charge_discharge_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="TStat Common Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
            ]
        )

    db.add_data_channels(
        [
            DataChannelGt(
                Name=H0CN.vdc_relay_state,
                DisplayName="5V DC Bus Relay State",
                AboutNodeName=H0N.vdc_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.vdc_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.tstat_common_relay_state,
                DisplayName="TStat Common Relay State",
                AboutNodeName=H0N.tstat_common_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.tstat_common_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.charge_discharge_relay_state,
                DisplayName="Charge/Discharge Relay State",
                AboutNodeName=H0N.store_charge_discharge_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.charge_discharge_relay_state)
            )
        ]
    )