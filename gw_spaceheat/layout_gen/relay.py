from typing import List
from gwproto.enums import ActorClass, MakeModel, Unit, RelayWiringConfig, TelemetryName, ChangeRelayState, ChangeAquastatControl, ChangeHeatcallSource, ChangeHeatPumpControl, PrimaryPumpControl, ChangeStoreFlowRelay
from gwproto.named_types import I2cMultichannelDtRelayComponentGt
from pydantic import BaseModel
from gwproto.named_types.component_attribute_class_gt import ComponentAttributeClassGt
from gwproto.named_types import RelayActorConfig
from data_classes.house_0_names import H0N, H0CN, House0RelayIdx
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
    if not db.component_id_by_alias(component_display_name):
        config_list = [
                RelayActorConfig(
                    ChannelName=H0CN.vdc_relay_state,
                    RelayIdx=House0RelayIdx.vdc,
                    ActorName=H0N.vdc_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyClosed,
                    EventType=ChangeRelayState.enum_name(),
                    DeEnergizingEvent=ChangeRelayState.CloseRelay,
                    EnergizingEvent=ChangeRelayState.OpenRelay,
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
                    EventType=ChangeRelayState.enum_name(),
                    DeEnergizingEvent=ChangeRelayState.CloseRelay,
                    EnergizingEvent=ChangeRelayState.OpenRelay,
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
                    EventType=ChangeStoreFlowRelay.enum_name(),
                    DeEnergizingEvent=ChangeStoreFlowRelay.DischargeStore,
                    EnergizingEvent=ChangeStoreFlowRelay.ChargeStore,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.hp_failsafe_relay_state,
                    RelayIdx=House0RelayIdx.hp_failsafe,
                    ActorName=H0N.hp_failsafe_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.DoubleThrow,
                    EventType=ChangeHeatPumpControl.enum_name(),
                    DeEnergizingEvent=ChangeHeatPumpControl.SwitchToTankAquastat,
                    EnergizingEvent=ChangeHeatPumpControl.SwitchToScada,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.hp_scada_ops_relay_state,
                    RelayIdx=House0RelayIdx.hp_scada_ops,
                    ActorName=H0N.hp_scada_ops_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyClosed,
                    EventType=ChangeRelayState.enum_name(),
                    DeEnergizingEvent=ChangeRelayState.CloseRelay,
                    EnergizingEvent=ChangeRelayState.OpenRelay,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.aquastat_ctrl_relay_state,
                    RelayIdx=House0RelayIdx.aquastat_ctrl,
                    ActorName=H0N.aquastat_ctrl_relay,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.DoubleThrow,
                    EventType=ChangeAquastatControl.enum_name(),
                    DeEnergizingEvent=ChangeAquastatControl.SwitchToBoiler,
                    EnergizingEvent=ChangeAquastatControl.SwitchToScada,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.store_pump_failsafe_relay_state,
                    RelayIdx=House0RelayIdx.store_pump_failsafe,
                    ActorName=H0N.store_pump_failsafe,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyOpen,
                    EventType=ChangeRelayState.enum_name(),
                    DeEnergizingEvent=ChangeRelayState.OpenRelay,
                    EnergizingEvent=ChangeRelayState.CloseRelay,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.primary_pump_failsafe_relay_state,
                    RelayIdx=House0RelayIdx.primary_pump_failsafe,
                    ActorName=H0N.primary_pump_failsafe,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.DoubleThrow,
                    EventType=PrimaryPumpControl.enum_name(),
                    DeEnergizingEvent=PrimaryPumpControl.HeatPump,
                    EnergizingEvent=PrimaryPumpControl.Scada,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
                RelayActorConfig(
                    ChannelName=H0CN.primary_pump_scada_ops_relay_state,
                    RelayIdx=House0RelayIdx.primary_pump_ops,
                    ActorName=H0N.primary_pump_scada_ops,
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.NormallyOpen,
                    EventType=ChangeRelayState.enum_name(),
                    DeEnergizingEvent=ChangeRelayState.OpenRelay,
                    EnergizingEvent=ChangeRelayState.CloseRelay,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),

        ]
        
        # Add 2 relays for each thermostat zone
        IDX = 17
        ChangeHeatcallSource
        zone_names = db.misc["ZoneList"]
        for i in range(len(zone_names)):
            zone = zone_names[i]
            RelayActorConfig(
                    ChannelName=f"zone{i+1}-{zone.lower}-failsafe-relay{IDX+2*i}",
                    RelayIdx=IDX+2*i,
                    ActorName=f"relay{IDX+2*i}",
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.DoubleThrow,
                    EventType=ChangeHeatcallSource.enum_name(),
                    DeEnergizingEvent=ChangeHeatcallSource.SwitchToWallThermostat,
                    EnergizingEvent=ChangeHeatcallSource.SwitchToScada,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),
        RelayActorConfig(
                    ChannelName=f"zone{i+1}-{zone.lower}-failsafe-relay{IDX+2*i+1}",
                    RelayIdx=IDX+2*i+1,
                    ActorName=f"relay{IDX+2*i+1}",
                    PollPeriodMs=cfg.PollPeriodMs,
                    CapturePeriodS=cfg.CapturePeriodS,
                    WiringConfig=RelayWiringConfig.DoubleThrow,
                    EventType=ChangeHeatcallSource.enum_name(),
                    DeEnergizingEvent=ChangeHeatcallSource.SwitchToWallThermostat,
                    EnergizingEvent=ChangeHeatcallSource.SwitchToScada,
                    AsyncCapture=True,
                    Exponent=0,
                    Unit=Unit.Unitless
                ),

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
                    ShNodeId=db.make_node_id(H0N.pico_cycler),
                    Name=H0N.pico_cycler,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.pico_cycler}",
                    Handle=f"auto.{H0N.pico_cycler}",
                    ActorClass=ActorClass.PicoCycler,
                    DisplayName="Pico Cycler - responsible for power cycling the 5VDC bus"
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.vdc_relay),
                    Name=H0N.vdc_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.vdc_relay}",
                    Handle=f"auto.{H0N.pico_cycler}.{H0N.vdc_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="5VDC Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.tstat_common_relay),
                    Name=H0N.tstat_common_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.tstat_common_relay}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.tstat_common_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="TStat Common Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.store_charge_discharge_relay),
                    Name=H0N.store_charge_discharge_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.store_charge_discharge_relay}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.store_charge_discharge_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Store Charge/Discharge Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.hp_failsafe_relay),
                    Name=H0N.hp_failsafe_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.hp_failsafe_relay}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.hp_failsafe_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Hp Failsafe Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.hp_scada_ops_relay),
                    Name=H0N.hp_scada_ops_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.hp_scada_ops_relay}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.hp_scada_ops_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Hp Scada Ops Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.aquastat_ctrl_relay),
                    Name=H0N.aquastat_ctrl_relay,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.aquastat_ctrl_relay}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.aquastat_ctrl_relay}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Aquastat Ctrl Relay",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.store_pump_failsafe),
                    Name=H0N.store_pump_failsafe,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.store_pump_failsafe}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.store_pump_failsafe}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Store Pump Failsafe",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.primary_pump_failsafe),
                    Name=H0N.primary_pump_failsafe,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.primary_pump_failsafe}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.primary_pump_failsafe}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Primary Pump Failsafe",
                    ComponentId=db.component_id_by_alias(component_display_name)
                ),
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(H0N.primary_pump_scada_ops),
                    Name=H0N.primary_pump_scada_ops,
                    ActorHierarchyName=f"{H0N.primary_scada}.{H0N.primary_pump_scada_ops}",
                    Handle=f"auto.{H0N.home_alone}.{H0N.primary_pump_scada_ops}",
                    ActorClass=ActorClass.Relay,
                    DisplayName="Primary Pump SCADA Ops",
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
            ),
            DataChannelGt(
                Name=H0CN.hp_failsafe_relay_state,
                DisplayName="Hp Failsafe Relay State",
                AboutNodeName=H0N.hp_failsafe_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.hp_failsafe_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.hp_scada_ops_relay_state,
                DisplayName="Hp Scada Ops Relay State",
                AboutNodeName=H0N.hp_scada_ops_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.hp_scada_ops_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.aquastat_ctrl_relay_state,
                DisplayName="Aquastat Control Relay State",
                AboutNodeName=H0N.aquastat_ctrl_relay,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.aquastat_ctrl_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.store_pump_failsafe_relay_state,
                DisplayName="Store Pump Failsafe Relay State",
                AboutNodeName=H0N.store_pump_failsafe,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.store_pump_failsafe_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.primary_pump_failsafe_relay_state,
                DisplayName="Primary Pump Failsafe Relay State",
                AboutNodeName=H0N.primary_pump_failsafe,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.primary_pump_failsafe_relay_state)
            ),
            DataChannelGt(
                Name=H0CN.primary_pump_scada_ops_relay_state,
                DisplayName="Primary Pump SCADA Ops Relay State",
                AboutNodeName=H0N.primary_pump_scada_ops,
                CapturedByNodeName=H0N.relay_multiplexer,
                TelemetryName=TelemetryName.RelayState,
                TerminalAssetAlias=db.terminal_asset_alias,
                Id=db.make_channel_id(H0CN.primary_pump_scada_ops_relay_state)
            )
        ]
    )