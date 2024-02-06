from gwproto.enums import ActorClass
from gwproto.enums import Role
from gwproto.types import HubitatPollerCacGt
from gwproto.types import HubitatPollerComponentGt
from gwproto.type_helpers import HubitatPollerGt
from gwproto.type_helpers import MakerAPIAttributeGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types.hubitat_gt import HubitatGt
from pydantic import BaseModel
from pydantic import root_validator

from layout_gen import LayoutDb
from layout_gen.hubitat import add_hubitat

class AttributeGenCfg(BaseModel):
    attribute_gt: MakerAPIAttributeGt
    display_name: str
    role: Role

class HubitatPollerGenCfg(BaseModel):
    node_name: str
    display_name: str = ""
    hubitat: HubitatGt
    device_id: int
    attributes: list[AttributeGenCfg] = []
    role: Role = Role.MultiChannelAnalogTempSensor
    poll_period_seconds: float = 60
    enabled: bool = True

    @root_validator
    def _root_validator(cls, values):
        for attribute in values["attributes"]:
            attribute.attribute_gt.node_name = (
                f"{values['node_name']}.{attribute.attribute_gt.node_name}"
            )
        return values

class HubitatThermostatGenCfg(BaseModel):
    node_name: str
    display_name: str = ""
    hubitat: HubitatGt
    device_id: int
    poll_period_seconds: float = 60
    enabled: bool = True

def add_hubitat_poller(
    db: LayoutDb,
    poller: HubitatPollerGenCfg,
) -> None:
    hubitat_alias = add_hubitat(db, poller.hubitat)
    cac_type = "hubitat.poller.cac.gt"
    if not db.cac_id_by_type(cac_type):
        db.add_cacs(
            [
                HubitatPollerCacGt(
                    ComponentAttributeClassId=db.make_cac_id(cac_type),
                    DisplayName="Hubitat Poller Cac",
                ),
            ]
        )
    db.add_components(
        [
            HubitatPollerComponentGt(
                ComponentId=db.make_component_id(poller.display_name),
                ComponentAttributeClassId=db.cac_id_by_type(cac_type),
                DisplayName=poller.display_name,
                Poller=HubitatPollerGt(
                    hubitat_component_id=db.component_id_by_alias(hubitat_alias),
                    device_id=poller.device_id,
                    attributes=[
                        attribute.attribute_gt
                        for attribute in poller.attributes
                    ],
                    enabled=poller.enabled,
                    poll_period_seconds=poller.poll_period_seconds,
                )
            ),
        ]
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(poller.node_name),
                Alias=poller.node_name,
                ActorClass=ActorClass.HubitatPoller,
                Role=poller.role,
                DisplayName=poller.display_name,
                ComponentId=db.component_id_by_alias(poller.display_name)
            )
        ] + [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(attribute.attribute_gt.node_name),
                Alias=attribute.attribute_gt.node_name,
                ActorClass=ActorClass.NoActor,
                Role=attribute.role,
                DisplayName=attribute.display_name,
            )
            for attribute in poller.attributes
        ]
    )


def add_hubitat_thermostat(
    db: LayoutDb,
    thermostat: HubitatThermostatGenCfg,
) -> None:
    add_hubitat_poller(
        db,
        HubitatPollerGenCfg(
            node_name=thermostat.node_name,
            display_name=thermostat.display_name,
            hubitat=thermostat.hubitat,
            device_id=thermostat.device_id,
            attributes=[
                AttributeGenCfg(
                    attribute_gt=MakerAPIAttributeGt(
                        attribute_name="temperature",
                        node_name="temp",
                        telemetry_name_gt_enum_symbol="793505aa",
                        unit_gt_enum_symbol="7d8832f8",
                    ),
                    display_name=thermostat.display_name + " Temperature",
                    role=Role.RoomTempSensor,
                ),
                AttributeGenCfg(
                    attribute_gt=MakerAPIAttributeGt(
                        attribute_name="heatingSetpoint",
                        node_name="set",
                        telemetry_name_gt_enum_symbol="793505aa",
                        unit_gt_enum_symbol="7d8832f8",
                    ),
                    display_name=thermostat.display_name + " Heating Set Point",
                    role=Role.Unknown,
                ),
            ],
            poll_period_seconds=thermostat.poll_period_seconds,
            enabled=thermostat.enabled,
        )
    )