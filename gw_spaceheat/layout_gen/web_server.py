from gwproto.types import WebServerGt
from gwproto.types.web_server_cac_gt import WebServerCacGt
from gwproto.types.web_server_component_gt import WebServerComponentGt

from layout_gen import LayoutDb

def add_web_server(
    db: LayoutDb,
    web_server: WebServerGt
) -> WebServerComponentGt:
    cac_type = "web.server.cac.gt"
    if not db.cac_id_by_type(cac_type):
        db.add_cacs(
            [
                WebServerCacGt(
                    ComponentAttributeClassId=db.make_cac_id(cac_type),
                    DisplayName="Web Server CAC",
                ),
            ]
        )
    component_alias = f"Web Server {web_server.Name}"
    if not db.component_id_by_alias(component_alias):
        db.add_components(
            [
                WebServerComponentGt(
                    ComponentId=db.make_component_id(component_alias),
                    ComponentAttributeClassId=db.cac_id_by_type(cac_type),
                    DisplayName=component_alias,
                    WebServer=web_server,
                ),
            ]
        )
    web_server_component_gt = db.components_by_id[db.component_id_by_alias(component_alias)]
    assert isinstance(web_server_component_gt, WebServerComponentGt)
    return web_server_component_gt
