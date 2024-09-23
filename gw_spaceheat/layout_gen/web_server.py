from gwproto.enums import MakeModel
from gwproto.type_helpers import WebServerGt
from gwproto.types.component_attribute_class_gt import ComponentAttributeClassGt
from gwproto.types.web_server_component_gt import WebServerComponentGt

from layout_gen import LayoutDb

def add_web_server(
    db: LayoutDb,
    web_server: WebServerGt
) -> WebServerComponentGt:
    cac_type = "web.server.cac.gt"
    if not db.cac_id_by_make_model(cac_type):
        db.add_cacs(
            [
                ComponentAttributeClassGt(
                    ComponentAttributeClassId=db.make_cac_id(cac_type),
                    DisplayName="Web Server CAC",
                    MakeModel=MakeModel.UNKNOWNMAKE__UNKNOWNMODEL,
                ),
            ]
        )
    component_alias = f"Web Server {web_server.Name}"
    if not db.component_id_by_alias(component_alias):
        db.add_components(
            [
                WebServerComponentGt(
                    ComponentId=db.make_component_id(component_alias),
                    ComponentAttributeClassId=db.cac_id_by_make_model(cac_type),
                    DisplayName=component_alias,
                    WebServer=web_server,
                ),
            ]
        )
    web_server_component_gt = db.components_by_id[db.component_id_by_alias(component_alias)]
    assert isinstance(web_server_component_gt, WebServerComponentGt)
    return web_server_component_gt
