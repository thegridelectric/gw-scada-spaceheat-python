"""Test communication issues"""
import argparse
import asyncio
from typing import cast
from typing import Optional

from config import MQTTClient
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from logging_setup import setup_logging
from proactor import Proactor
from tests.atn import Atn2
from tests.atn import AtnSettings
from tests.utils import Scada2Recorder
from tests.utils.fragment_runner import AsyncFragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from tests.utils import await_for

import pytest
from paho.mqtt.client import MQTT_ERR_CONN_LOST

class CommTestHelper:
    SCADA: str = "a.s"
    ATN: str = "a"

    proactors: dict[str, Proactor]
    settings: ScadaSettings
    atn_settings: AtnSettings
    verbose: bool
    layout: HardwareLayout

    def __init__(
        self,
        settings: Optional[ScadaSettings] = None,
        atn_settings: Optional[AtnSettings] = None,
        verbose: bool = False,
        add_scada: bool = False,
        add_atn: bool = False,
        start_scada: bool = False,
        start_atn: bool = False,
    ):
        self.settings = ScadaSettings() if settings is None else settings
        self.atn_settings = AtnSettings() if atn_settings is None else atn_settings
        self.verbose = verbose
        self.layout = HardwareLayout.load(self.settings.paths.hardware_layout)
        self.setup_logging()
        self.proactors = dict()
        if add_scada or start_scada:
            self.add_scada()
            if start_scada:
                self.start_scada()
        if add_atn or start_atn:
            self.add_atn()
            if start_atn:
                self.start_atn()

    def start_scada(self) -> "CommTestHelper":
        return self.start_proactor(self.SCADA)

    def start_atn(self) -> "CommTestHelper":
        return self.start_proactor(self.ATN)

    def start_proactor(self, name: str) ->  "CommTestHelper":
        asyncio.create_task(self.proactors[name].run_forever(), name=f"{name}_run_forever")
        return self

    def start(self) -> "CommTestHelper":
        for proactor_name in self.proactors:
            self.start_proactor(proactor_name)
        return self

    def add_scada(self) -> "CommTestHelper":
        proactor = Scada2Recorder(
            self.SCADA,
            settings=self.settings,
            hardware_layout=self.layout,
        )
        self.proactors[proactor.name] = proactor
        return self

    def add_atn(self) -> "CommTestHelper":
        proactor = Atn2(
            self.ATN,
            settings=self.atn_settings,
            hardware_layout=self.layout,
        )
        self.proactors[proactor.name] = proactor
        return self

    @property
    def scada(self) -> Scada2Recorder:
        return cast(Scada2Recorder, self.proactors[self.SCADA])

    @property
    def atn(self) -> Atn2:
        return cast(Atn2, self.proactors[self.ATN])

    def setup_logging(self):
        self.settings.paths.mkdirs(parents=True)
        self.atn_settings.paths.mkdirs(parents=True)
        errors = []
        args = argparse.Namespace(verbose=self.verbose)
        setup_logging(args, self.settings, errors, add_screen_handler=True)
        assert not errors
        setup_logging(args, cast(ScadaSettings, self.atn_settings), errors, add_screen_handler=False)
        assert not errors

    async def stop_and_join(self):
        for proactor in self.proactors.values():
            # noinspection PyBroadException
            try:
                proactor.stop()
            except:
                pass
        for proactor in self.proactors.values():
            # noinspection PyBroadException
            try:
                await proactor.join()
            except:
                pass

    async def __aenter__(self) -> "CommTestHelper":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop_and_join()

@pytest.skip
@pytest.mark.asyncio
async def test_no_broker():
    no_broker = MQTTClient(host="www.foo.com")
    async with CommTestHelper(
        settings=ScadaSettings(
            gridworks_mqtt=no_broker,
            local_mqtt=no_broker,
        ),
        start_scada=True,
    ):
        for i in range(10):
            print(f"{i}...")
            await asyncio.sleep(1)

@pytest.skip
@pytest.mark.asyncio
async def test_no_mqtt_no_atn():
    async with CommTestHelper(start_scada=True) as h:
        for i in range(2):
            print(f"{i}...")
            await asyncio.sleep(1)
        print(h.scada.summary_str())

@pytest.mark.asyncio
async def test_simple_resubscribe_on_comm_restore2(tmp_path, monkeypatch, request):

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        async def async_run(self):
            link_stats = self.runner.actors.scada2.stats.links["gridworks"]
            summary_str = self.runner.actors.scada2.summary_str
            await await_for(
                lambda: link_stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 0,
                1,
                "ERROR waiting for gw_client subscribe 1",
                err_str_f=summary_str
            )
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0

            # Tell client we lost comm.
            self.runner.actors.scada2._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for disconnect
            await await_for(
                lambda: link_stats.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] > 0,
                1,
                "ERROR waiting for gw_client disconnect",
                err_str_f=summary_str
            )
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1

            # Wait for re-subscribe
            await await_for(
                lambda: link_stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 1,
                5,
                "ERROR waiting for gw_client subscribe 2",
                err_str_f=summary_str
            )
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            assert link_stats.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1

    await AsyncFragmentRunner.async_run_fragment(
        Fragment,
        tag=request.node.name,
        args=argparse.Namespace(verbose=True)
    )
