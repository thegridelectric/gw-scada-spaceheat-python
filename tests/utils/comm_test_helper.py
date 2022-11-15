import argparse
import asyncio
import logging
from typing import cast
from typing import Optional

from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from logging_setup import setup_logging
from proactor import Proactor
from tests.atn import Atn2
from tests.atn import AtnSettings
from tests.utils import Scada2Recorder


class CommTestHelper:
    SCADA: str = "a.s"
    ATN: str = "a"

    proactors: dict[str, Proactor]
    settings: ScadaSettings
    atn_settings: AtnSettings
    verbose: bool
    lifecycle_logging: bool
    layout: HardwareLayout

    def __init__(
        self,
        settings: Optional[ScadaSettings] = None,
        atn_settings: Optional[AtnSettings] = None,
        verbose: bool = False,
        lifecycle_logging: bool = False,
        add_scada: bool = False,
        add_atn: bool = False,
        start_scada: bool = False,
        start_atn: bool = False,
    ):
        self.settings = ScadaSettings() if settings is None else settings
        self.atn_settings = AtnSettings() if atn_settings is None else atn_settings
        self.verbose = verbose
        self.lifecycle_logging = lifecycle_logging
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

    def remove_proactor(self, name: str) -> Proactor:
        return self.proactors.pop(name)

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

    def remove_scada(self) -> "CommTestHelper":
        self.remove_proactor(self.SCADA)
        return self

    def remove_atn(self) -> "CommTestHelper":
        self.remove_proactor(self.ATN)
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
        if not self.verbose and not self.lifecycle_logging:
            self.settings.logging.levels.lifecycle = logging.WARNING
        args = argparse.Namespace(verbose=self.verbose)
        setup_logging(args, self.settings, errors, add_screen_handler=True, root_gets_handlers=False)
        assert not errors
        setup_logging(args, cast(ScadaSettings, self.atn_settings), errors, add_screen_handler=False, root_gets_handlers=False)
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
        if exc is not None:
            logging.getLogger("gridworks").error(
                "CommTestHelper caught error %s.\nWorking log dirs:\n\t[%s]\n\t[%s]",
                exc,
                self.settings.paths.log_dir,
                self.atn_settings.paths.log_dir,
            )
