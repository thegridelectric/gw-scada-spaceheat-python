from gwproto.types import HubitatCacGt
from gwproto.types import HubitatComponentGt
from gwproto.types.hubitat_gt import HubitatGt

from layout_gen.layout_db import LayoutDb

def add_hubitat(
    db: LayoutDb,
    hubitat: HubitatGt
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
    hubitat_alias = f"Hubitat {hubitat.MacAddress[-8:]}"
    if not db.component_id_by_alias(hubitat_alias):
        db.add_components(
            [
                HubitatComponentGt(
                    ComponentId=db.make_component_id(hubitat_alias),
                    ComponentAttributeClassId=db.make_cac_id(cac_type),
                    DisplayName=hubitat_alias,
                    Hubitat=hubitat,
                ),
            ]
    )
    return hubitat_alias
