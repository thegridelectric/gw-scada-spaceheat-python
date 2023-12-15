import uuid
from typing import Tuple

from gwproto.enums import ActorClass
from gwproto.enums import Role
from gwproto.types import FibaroSmartImplantCacGt
from gwproto.types import FibaroSmartImplantComponentGt
from gwproto.types import FibaroTempSensorSettingsGt
from gwproto.types import HubitatCacGt
from gwproto.types import HubitatComponentGt
from gwproto.types import HubitatTankCacGt
from gwproto.types import HubitatTankComponentGt
from gwproto.types import HubitatTankSettingsGt
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
    if not db.cac_id_by_type("fibaro.smart.implant.cac.gt"):
        db.add_cacs(
            [
                FibaroSmartImplantCacGt(
                    ComponentAttributeClassId=str(uuid.uuid4()),
                    DisplayName="Fibaro SmartImplant FGBS-222",
                    Model="FGBS-222 v5.2",
                ),
            ]
        )
    if not db.cac_id_by_type("hubitat.cac.gt"):
        db.add_cacs(
            [
                HubitatCacGt(
                    ComponentAttributeClassId=str(uuid.uuid4()),
                    DisplayName="Hubitat Elevation C-7",
                ),
            ]
        )
    if not db.cac_id_by_type("hubitat.tank.cac.gt"):
        db.add_cacs(
            [
                HubitatTankCacGt(
                    ComponentAttributeClassId=str(uuid.uuid4()),
                    DisplayName="Hubitat Tank Module",
                ),
            ]
        )

    hubitat_alias = f"Hubitat {hubitat.MacAddress[-8:]}"
    if not db.component_id_by_alias(hubitat_alias):
        db.add_components(
            [
                HubitatComponentGt(
                    ComponentId=str(uuid.uuid4()),
                    ComponentAttributeClassId=db.cac_id_by_type("hubitat.cac.gt"),
                    DisplayName=hubitat_alias,
                    Hubitat=hubitat,
                ),
            ]
    )
    db.add_components(
        [
            FibaroSmartImplantComponentGt(
                ComponentId=str(uuid.uuid4()),
                ComponentAttributeClassId=db.cac_id_by_type(
                    "fibaro.smart.implant.cac.gt"
                ),
                DisplayName=fibaro_a.alias(),
                ZWaveDSK=fibaro_a.ZWaveDSK,
            ),
            FibaroSmartImplantComponentGt(
                ComponentId=str(uuid.uuid4()),
                ComponentAttributeClassId=db.cac_id_by_type(
                    "fibaro.smart.implant.cac.gt"
                ),
                DisplayName=fibaro_b.alias(),
                ZWaveDSK=fibaro_b.ZWaveDSK,
            ),
        ]
    )
    db.add_components(
        [
            HubitatTankComponentGt(
                ComponentId=str(uuid.uuid4()),
                ComponentAttributeClassId=db.cac_id_by_type("hubitat.tank.cac.gt"),
                DisplayName=tank.component_alias(),
                Tank=HubitatTankSettingsGt(
                    hubitat_component_id=db.component_id_by_alias(hubitat_alias),
                    devices=[
                        FibaroTempSensorSettingsGt(
                            stack_depth=1,
                            device_id=tank.DeviceIds[0],
                            fibaro_component_id=db.component_id_by_alias(fibaro_a.alias()),
                            analog_input_id=1,
                            tank_label=f"{tank.SN} A1 (Thermistor #1 TANK TOP)",
                            enabled=True,
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=2,
                            device_id=tank.DeviceIds[1],
                            fibaro_component_id=db.component_id_by_alias(fibaro_a.alias()),
                            analog_input_id=2,
                            tank_label=f"{tank.SN} A2 (Thermistor #2)",
                            enabled=True,
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=3,
                            device_id=tank.DeviceIds[2],
                            fibaro_component_id=db.component_id_by_alias(fibaro_b.alias()),
                            analog_input_id=1,
                            tank_label=f"{tank.SN} B1 (Thermistor #3)",
                            enabled=True,
                        ),
                        FibaroTempSensorSettingsGt(
                            stack_depth=4,
                            device_id=tank.DeviceIds[3],
                            fibaro_component_id=db.component_id_by_alias(fibaro_b.alias()),
                            analog_input_id=2,
                            tank_label=f"{tank.SN} B2 (Thermistor #4 TANK BOTTOM)",
                            enabled=True,
                        ),
                    ]
                ),
            ),
        ]
    )

    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=self.make_node_id(),
                Alias=tank.NodeAlias,
                ActorClass=ActorClass.HubitatTankModule,
                Role=Role.MultiChannelAnalogTempSensor,
                DisplayName=tank.node_display_name(),
                ComponentId=db.component_id_by_alias(tank.component_alias())
            ),
            SpaceheatNodeGt(
                ShNodeId=self.make_node_id(),
                Alias=tank.thermistor_node_alias(1),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(1),
            ),
            SpaceheatNodeGt(
                ShNodeId=self.make_node_id(),
                Alias=tank.thermistor_node_alias(2),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(2),
            ),
            SpaceheatNodeGt(
                ShNodeId=self.make_node_id(),
                Alias=tank.thermistor_node_alias(3),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(3),
            ),

            SpaceheatNodeGt(
                ShNodeId=self.make_node_id(),
                Alias=tank.thermistor_node_alias(4),
                ActorClass=ActorClass.NoActor,
                Role=Role.TankWaterTempSensor,
                DisplayName=tank.thermistor_node_display_name(4),
            ),
        ]
    )

