from gwproto.enums import ActorClass
from gwproto.enums import MakeModel
from gwproto.enums import Role
from gwproto.type_helpers import CACS_BY_MAKE_MODEL
from gwproto.types import ComponentAttributeClassGt
from gwproto.types import HubitatComponentGt
from gwproto.types import SpaceheatNodeGt
from gwproto.types.hubitat_gt import HubitatGt

from layout_gen.layout_db import LayoutDb
from data_classes.house_0 import H0N

def add_hubitat(
    db: LayoutDb,
    hubitat: HubitatGt,
) -> str:
    make_model = MakeModel.HUBITAT__C7__LAN1
    if not db.cac_id_by_alias(make_model):
        db.add_cacs(
            [
                ComponentAttributeClassGt(
                    ComponentAttributeClassId=CACS_BY_MAKE_MODEL[make_model],
                    DisplayName="Hubitat Elevation C-7",
                    MakeModel=make_model,
                ),
            ]
        )
    hubitat_component_alias = f"Hubitat {hubitat.MacAddress[-8:]}"
    if not db.component_id_by_alias(hubitat_component_alias):
        db.add_components(
            [
                HubitatComponentGt(
                    ComponentId=db.make_component_id(hubitat_component_alias),
                    ComponentAttributeClassId=db.cac_id_by_alias(make_model),
                    DisplayName=hubitat_component_alias,
                    Hubitat=hubitat,
                    HwUid=hubitat.MacAddress[-8:].replace(":", "").lower(),
                    ConfigList=[],
                )
            ]
    )
    db.add_nodes(
        [
            SpaceheatNodeGt(
                ShNodeId=db.make_node_id(H0N.hubitat),
                Alias=H0N.hubitat,
                ActorClass=ActorClass.Hubitat,
                Role=Role.Unknown,
                DisplayName=hubitat_component_alias,
                ComponentId=db.component_id_by_alias(hubitat_component_alias),
            )
        ]
    )
    return hubitat_component_alias
