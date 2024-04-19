from gwproto.enums import ActorClass
from gwproto.enums import Role
from gwproto.types import HubitatCacGt
from gwproto.types import HubitatComponentGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types.hubitat_gt import HubitatGt

from layout_gen.layout_db import LayoutDb

def add_hubitat(
    db: LayoutDb,
    hubitat: HubitatGt,
    hubitat_node_alias: str = "",
) -> str:
    cac_type = "hubitat.cac.gt"
    if not db.cac_id_by_type(cac_type):
        db.add_cacs(
            [
                HubitatCacGt(
                    ComponentAttributeClassId=db.make_cac_id(cac_type),
                    DisplayName="Hubitat Elevation C-7",
                ),
            ]
        )
    hubitat_component_alias = f"Hubitat {hubitat.MacAddress[-8:]}"
    if not db.component_id_by_alias(hubitat_component_alias):
        db.add_components(
            [
                HubitatComponentGt(
                    ComponentId=db.make_component_id(hubitat_component_alias),
                    ComponentAttributeClassId=db.cac_id_by_type(cac_type),
                    DisplayName=hubitat_component_alias,
                    Hubitat=hubitat,
                ),
            ]
    )
    if not hubitat_node_alias:
        hubitat_node_alias = f"a.hubitat.{hubitat.MacAddress[-8:]}".replace(":", "")
    if not db.node_id_by_alias(hubitat_node_alias):
        db.add_nodes(
            [
                SpaceheatNodeGt(
                    ShNodeId=db.make_node_id(hubitat_node_alias),
                    Alias=hubitat_node_alias,
                    ActorClass=ActorClass.Hubitat,
                    Role=Role.Unknown,
                    DisplayName=hubitat_component_alias,
                    ComponentId=db.component_id_by_alias(hubitat_component_alias),
                )
            ]
        )
    return hubitat_component_alias
