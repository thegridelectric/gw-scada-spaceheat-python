import uuid

from gwproto.types import HubitatCacGt
from gwproto.types import HubitatComponentGt
from gwproto.types.hubitat_gt import HubitatGt

from layout_gen import LayoutDb

def add_hubitat(
    db: LayoutDb,
    hubitat: HubitatGt
) -> str:
    if not db.cac_id_by_type("hubitat.cac.gt"):
        db.add_cacs(
            [
                HubitatCacGt(
                    ComponentAttributeClassId=str(uuid.uuid4()),
                    DisplayName="Hubitat Elevation C-7",
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
    return hubitat_alias
