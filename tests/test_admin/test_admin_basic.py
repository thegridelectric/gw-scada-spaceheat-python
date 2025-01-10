from pathlib import Path
from typing import Optional

import pytest
from gwproactor_test import await_for
from gwproactor_test import copy_keys
from textual.widgets import DataTable

from actors.config import AdminLinkSettings
from actors.config import ScadaSettings
from admin.settings import AdminClientSettings
from admin.watch import relay_app
from admin.watch.widgets.mqtt import MqttState

from tests.utils.scada_comm_test_helper import ScadaCommTestHelper

class AdminScadaCommTestHelper(ScadaCommTestHelper):
    """Helper for the simulated scada we test the admin app against."""

    def __init__(self, **kwargs):
        if "child_settings" not in kwargs:
            kwargs["child_settings"] = ScadaSettings(
                admin=AdminLinkSettings(enabled=True)
            )
        super().__init__(**kwargs)

    async def await_scada_active_for_send(self) -> None:
        scada_uplink = self.child.links.link(self.child.upstream_client) # noqa
        await await_for(
            lambda: scada_uplink.active_for_send,
            3,
            "Scada never went active_for_send",
            err_str_f=self.summary_str
        )

class RelaysAppRecorder(relay_app.RelaysApp):

    CSS_PATH = Path(relay_app.__file__).parent / relay_app.RelaysApp.CSS_PATH

    def mqtt_state(self) -> MqttState:
        return self.query_one("#mqtt_state", MqttState)

    def mqtt_active(self) -> bool:
        return self.mqtt_state().mqtt_state == "active"

    def scada_active(self) -> bool:
        return self.mqtt_active() and self.mqtt_state().layout_count > 0

    def num_relays(self) -> int:
        return self.query_one("#relays_table", DataTable).row_count

def make_admin_app(
        settings: Optional[AdminClientSettings] = None
) -> RelaysAppRecorder:
    if settings is None:
        settings = AdminClientSettings(
            target_gnode="d1.isone.ct.newhaven.orange1.scada",
        )
    copy_keys("admin", settings)
    return RelaysAppRecorder(settings=settings)

@pytest.mark.asyncio
async def test_admin_mqtt_connect() -> None:
    admin_app = make_admin_app()
    async with admin_app.run_test():
        await await_for(
            admin_app.mqtt_active,
            1,
            "Admin app could not connect to MQTT broker",
        )

@pytest.mark.asyncio
async def test_admin_scada_connect() -> None:
    async with AdminScadaCommTestHelper(
        start_child=True,
        child_settings=ScadaSettings(admin=AdminLinkSettings(enabled=True)),
    ) as h:
        await h.await_scada_active_for_send()
        admin_app = make_admin_app()
        async with admin_app.run_test():
            await await_for(
                admin_app.scada_active,
                1,
                "Admin app could not connect to scada correctly",
            )
