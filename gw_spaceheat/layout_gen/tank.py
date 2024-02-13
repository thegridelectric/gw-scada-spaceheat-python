from typing import Optional
from typing import Tuple

from gwproto.enums import ActorClass
from gwproto.enums import Role
from gwproto.types import FibaroSmartImplantCacGt
from gwproto.types import FibaroSmartImplantComponentGt
from gwproto.type_helpers import FibaroTempSensorSettingsGt
from gwproto.types import HubitatCacGt
from gwproto.types import HubitatComponentGt
from gwproto.types import HubitatTankCacGt
from gwproto.types import HubitatTankComponentGt
from gwproto.type_helpers import HubitatTankSettingsGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types.hubitat_gt import HubitatGt
from pydantic import BaseModel

from layout_gen import LayoutDb

class FibaroGenCfg(BaseModel):
    SN: str
    ZWaveDSK: str

    def alias(self) -> str:
        return f"Fibaro Smart Implant {self.SN}"

class TankGenCfg(BaseModel):
    NodeAlias: str
    InHomeName: str
    SN: str
    DeviceIds: Tuple[int, int, int, int]
    DefaultPollPeriodSeconds: Optional[float] = None
    DevicePollPeriodSeconds: Tuple[float|None, float|None, float|None, float|None] = None, None, None, None

    def node_display_name(self) -> str:
        return f"Tank Module <{self.InHomeName}>"

    def component_alias(self) -> str:
        return f"Tank Module <{self.InHomeName}>  SN {self.SN}"

    def thermistor_node_alias(self, depth: int) -> str:
        return f"{self.NodeAlias}.temp.depth{depth}"

    def thermistor_node_display_name(self, depth: int) -> str:
        if depth == 1:
            extra = " (top)"
        elif depth == len(self.DeviceIds):
            extra = " (bottom)"
        else:
            extra = ""
        return f"{self.node_display_name()} temp sensor at depth {depth}{extra}"

def add_tank(
    db: LayoutDb,
    fibaro_a: FibaroGenCfg,
    fibaro_b: FibaroGenCfg,
    hubitat: HubitatGt,
    tank: TankGenCfg,
) -> None:
    fibaro_cac_type = "fibaro.smart.implant.cac.gt"
    if not db.cac_id_by_type(fibaro_cac_type):
        db.add_cacs(
            [
                FibaroSmartImplantCacGt(
                    ComponentAttributeClassId=db.make_cac_id(fibaro_cac_type),
                    DisplayName="Fibaro SmartImplant FGBS-222",
                    Model="FGBS-222 v5.2",
                ),
            ]
        )
    hubitat_cac_type = "hubitat.cac.gt"
    if not db.cac_id_by_type(hubitat_cac_type):
        db.add_cacs(
            [
                HubitatCacGt(
                    ComponentAttributeClassId=db.make_cac_id(hubitat_cac_type),
                    DisplayName="Hubitat Elevation C-7",
                ),
            ]
        )
    hubitat_tank_cac_type = "hubitat.tank.cac.gt"
    if not db.cac_id_by_type(hubitat_tank_cac_type):
        db.add_cacs(
            [
                HubitatTankCacGt(
                    ComponentAttributeClassId=db.make_cac_id(hubitat_tank_cac_type),
                    DisplayName="Hubitat Tank Module",
                ),
            ]
        )

    hubitat_alias = f"Hubitat {hubitat.MacAddress[-8:]}"
    if not db.component_id_by_alias(hubitat_alias):
        db.add_components(
            [
                HubitatComponentGt(
                    ComponentId=db.make_component_id(hubitat_alias),
                    ComponentAttributeClassId=db.cac_id_by_type(hubitat_cac_type),
                    DisplayName=hubitat_alias,
                    Hubitat=hubitat,
                ),
            ]
    )
    db.add_components(
        [
            FibaroSmartImplantComponentGt(
                ComponentId=db.make_component_id(fibaro_a.alias()),
                ComponentAttributeClassId=db.cac_id_by_type(fibaro_cac_type),
                DisplayName=fibaro_a.alias(),
                ZWaveDSK=fibaro_a.ZWaveDSK,
            ),
            FibaroSmartImplantComponentGt(
                ComponentId=db.make_component_id(fibaro_b.alias()),
                ComponentAttributeClassId=db.cac_id_by_type(fibaro_cac_type),
                DisplayName=fibaro_b.alias(),
                ZWaveDSK=fibaro_b.ZWaveDSK,
            ),
        ]
    )
    db.add_components(
        [
            HubitatTankComponentGt(
                ComponentId=db.make_component_id(tank.component_alias()),
                ComponentAttributeClassId=db.cac_id_by_type(hubitat_tank_cac_type),
                DisplayName=tank.component_alias(),
                Tank=HubitatTankSettingsGt(
                    hubitat_component_id=db.component_id_by_alias(hubitat_alias),
                    default_poll_period_seconds=tank.DefaultPollPeriodSeconds,
                    devices=[
                        FibaroTempSensorSettingsGt(
                            stack_depth=1,
                            device_id=tank.DeviceIds[0],
                            fibaro_component_id=db.component_id_by_alias(fibaro_a.alias()),
                            analog_input_id=1,
                            tank_label=f"{tank.SN} A1 (Thermistor #1 TANK TOP)",
                            enabled=True,
                            poll_period_seconds=tank.DevicePollPeriodSeconds[0],
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=2,
                            device_id=tank.DeviceIds[1],
                            fibaro_component_id=db.component_id_by_alias(fibaro_a.alias()),
                            analog_input_id=2,
                            tank_label=f"{tank.SN} A2 (Thermistor #2)",
                            enabled=True,
                            poll_period_seconds=tank.DevicePollPeriodSeconds[1],
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=3,
                            device_id=tank.DeviceIds[2],
                            fibaro_component_id=db.component_id_by_alias(fibaro_b.alias()),
                            analog_input_id=1,
                            tank_label=f"{tank.SN} B1 (Thermistor #3)",
                            enabled=True,
                            poll_period_seconds=tank.DevicePollPeriodSeconds[2],
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=4,
                            device_id=tank.DeviceIds[3],
                            fibaro_component_id=db.component_id_by_alias(fibaro_b.alias()),
                            analog_input_id=2,
                            tank_label=f"{tank.SN} B2 (Thermistor #4 TANK BOTTOM)",
                            enabled=True,
                            poll_period_seconds=tank.DevicePollPeriodSeconds[3],
                        ),
                    ]
                ),
            ),
        ]
    )

    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tank.NodeAlias),
                Alias=tank.NodeAlias,
                ActorClass=ActorClass.HubitatTankModule,
                Role=Role.MultiChannelAnalogTempSensor,
                DisplayName=tank.node_display_name(),
                ComponentId=db.component_id_by_alias(tank.component_alias())
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tank.thermistor_node_alias(1)),
                Alias=tank.thermistor_node_alias(1),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(1),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tank.thermistor_node_alias(2)),
                Alias=tank.thermistor_node_alias(2),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(2),
            ),
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tank.thermistor_node_alias(3)),
                Alias=tank.thermistor_node_alias(3),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(3),
            ),

            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(tank.thermistor_node_alias(4)),
                Alias=tank.thermistor_node_alias(4),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(4),
            ),
        ]
    )

