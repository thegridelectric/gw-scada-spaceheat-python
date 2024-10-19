from gwproto.types import PicoTankModuleComponentGt
from typing import List
from pydantic import BaseModel
from gwproto.property_format import SpaceheatName
from layout_gen import LayoutDb
from gwproto.types.component_attribute_class_gt import ComponentAttributeClassGt
from gwproto.types.data_channel_gt import DataChannelGt
from gwproto.enums import MakeModel, Unit, ActorClass, TelemetryName
from gwproto.types.channel_config import ChannelConfig
from gwproto.types import SpaceheatNodeGt
from gwproto.data_classes.house_0_names import H0N


class Tank2Cfg(BaseModel):
    SerialNumber: str
    PicoIds: List[str]
    ActorNodeName: SpaceheatName = "buffer"
    CapturePeriodS: int = 60
    AsyncCaptureDeltaMicroVolts: int = 2000
    Samples:int  = 1000
    NumSampleAverages:int = 10
    Enabled: bool = True
    SendMicroVolts: bool = False

    def component_display_name(self) -> str:
        return f"{self.ActorNodeName} PicoTankModule"



def add_tank2(
        db: LayoutDb,
        tank_cfg: Tank2Cfg
) -> None:
    if not db.cac_id_by_alias(MakeModel.GRIDWORKS__TANKMODULE2):
        db.add_cacs(
            [
                ComponentAttributeClassGt(
                    ComponentAttributeClassId=db.make_cac_id(MakeModel.GRIDWORKS__TANKMODULE2),
                    DisplayName="GridWorks TankModule2 (Uses 2 picos)",
                    MakeModel=MakeModel.GRIDWORKS__TANKMODULE2,
                ),
            ]
        )
    
    if not db.component_id_by_alias(tank_cfg.component_display_name):
        config_list = []
        for i in range(1,5):
            config_list.append(
                ChannelConfig(
                    ChannelName=f"{tank_cfg.ActorNodeName}-depth{i}",
                    PollPeriodMs=1000,
                    CapturePeriodS=tank_cfg.CapturePeriodS,
                    AsyncCapture=True,
                    AsyncCaptureDelta=tank_cfg.AsyncCaptureDeltaMicroVolts,
                    Exponent=3,
                    Unit=Unit.Celcius
                )
            )
        db.add_components(
            [
                PicoTankModuleComponentGt(
                    ComponentId=db.make_component_id(tank_cfg.component_display_name),
                    ComponentAttributeClassId=db.cac_id_by_alias(MakeModel.GRIDWORKS__TANKMODULE2),
                    DisplayName=tank_cfg.component_display_name(),
                    HwUid=tank_cfg.SerialNumber,
                    ConfigList=config_list,
                    PicoHwUidList=tank_cfg.PicoIds,
                    Enabled=tank_cfg.Enabled,
                    SendMicroVolts=tank_cfg.SendMicroVolts,
                    Samples=tank_cfg.Samples,
                    NumSampleAverages=tank_cfg.NumSampleAverages 
                ),
            ]
        )

        db.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(tank_cfg.ActorNodeName),
                    Name=tank_cfg.ActorNodeName,
                    ActorHierarchyName=f"{H0N.secondary_scada}.{tank_cfg.ActorNodeName}",
                    ActorClass=ActorClass.ApiTankModule,
                    DisplayName=f"{tank_cfg.ActorNodeName.capitalize()} Tank",
                    ComponentId=db.component_id_by_alias(tank_cfg.component_display_name())
                )
            ] + [
                SpaceheatNodeGt(
                ShNodeId=db.make_node_id(f"{tank_cfg.ActorNodeName}-depth{i}"),
                Name=f"{tank_cfg.ActorNodeName}-depth{i}",
                ActorClass=ActorClass.NoActor,
                DisplayName=f"{tank_cfg.ActorNodeName}-depth{i}",
                )
                for i in  range(1,5)
            ]
        )

        db.add_data_channels(
            [ DataChannelGt(
               Name=f"{tank_cfg.ActorNodeName}-depth{i}",
               DisplayName=f"{tank_cfg.ActorNodeName.capitalize()} Depth {i}",
               AboutNodeName=f"{tank_cfg.ActorNodeName}-depth{i}",
               CapturedByNodeName=tank_cfg.ActorNodeName,
               TelemetryName=TelemetryName.WaterTempCTimes1000,
               TerminalAssetAlias=db.terminal_asset_alias,
               Id=db.make_channel_id(f"{tank_cfg.ActorNodeName}-depth{i}")
               ) for i in range(1,5)
            ]
        )