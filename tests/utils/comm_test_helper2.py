import argparse
import asyncio
import logging
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Optional
from typing import Type
from typing import TypeVar

from proactor import ProactorSettings
from logging_setup import setup_logging
from proactor import Proactor

from tests.conftest import LoggerGuards
from tests.utils.proactor_recorder import RecorderInterface
from tests.utils.proactor_recorder import make_recorder_class
from tests.utils.proactor_recorder import ProactorT


@dataclass
class ProactorTestHelper:
    name: str
    settings: ProactorSettings
    kwargs: dict = field(default_factory = dict)
    proactor: Optional[RecorderInterface] = None

ChildT = TypeVar("ChildT", bound=Proactor)
ParentT = TypeVar("ParentT", bound=Proactor)
ChildSettingsT = TypeVar("ChildSettingsT", bound=ProactorSettings)
ParentSettingsT = TypeVar("ParentSettingsT", bound=ProactorSettings)


class CommTestHelper2:

    parent_t: Type[ProactorT]
    child_t: Type[Proactor]
    parent_settings_t: Type[ParentSettingsT]
    child_settings_t: Type[ProactorSettings]

    parent_recorder_t: Callable[..., RecorderInterface] = None
    child_recorder_t: Callable[..., RecorderInterface] = None

    parent_helper: ProactorTestHelper
    child_helper: ProactorTestHelper
    verbose: bool
    parent_on_screen: bool
    lifecycle_logging: bool
    logger_guards: LoggerGuards

    @classmethod
    def setup_class(cls):
        if cls.parent_recorder_t is None:
            cls.parent_recorder_t = make_recorder_class(cls.parent_t)
        if cls.child_recorder_t is None:
            cls.child_recorder_t = make_recorder_class(cls.child_t)

    def __init__(
        self,
        child_settings: Optional[ChildSettingsT] = None,
        parent_settings: Optional[ParentSettingsT] = None,
        verbose: bool = False,
        lifecycle_logging: bool = False,
        add_child: bool = False,
        add_parent: bool = False,
        start_child: bool = False,
        start_parent: bool = False,
        parent_on_screen: bool = False,
        child_name: str = "",
        parent_name: str = "",
        child_kwargs: Optional[dict] = None,
        parent_kwargs: Optional[dict] = None,
    ):
        self.setup_class()
        self.child_helper = ProactorTestHelper(
            child_name,
            self.child_settings_t() if child_settings is None else child_settings,
            dict() if child_kwargs is None else child_kwargs,

        )
        self.parent_helper = ProactorTestHelper(
            parent_name,
            self.parent_settings_t() if parent_settings is None else parent_settings,
            dict() if parent_kwargs is None else parent_kwargs,
        )
        self.verbose = verbose
        self.parent_on_screen = parent_on_screen
        self.lifecycle_logging = lifecycle_logging
        self.setup_logging()
        if add_child or start_child:
            self.add_child()
            if start_child:
                self.start_child()
        if add_parent or start_parent:
            self.add_parent()
            if start_parent:
                self.start_parent()

    @classmethod
    def _make(cls, recorder_t: Callable[..., RecorderInterface], helper: ProactorTestHelper) -> RecorderInterface:
        return recorder_t(
            helper.name,
            helper.settings,
            **helper.kwargs
        )

    def make_parent(self) -> RecorderInterface:
        return self._make(self.parent_recorder_t, self.parent_helper)

    def make_child(self) -> RecorderInterface:
        return self._make(self.child_recorder_t, self.child_helper)

    @property
    def parent(self) -> Optional[ProactorT]:
        return self.parent_helper.proactor

    @property
    def child(self) -> Optional[ProactorT]:
        return self.child_helper.proactor

    def start_child(self) -> "CommTestHelper2":
        if self.child is not None:
            self.start_proactor(self.child)
        return self

    def start_parent(self) -> "CommTestHelper2":
        if self.parent is not None:
            self.start_proactor(self.parent)
        return self

    def start_proactor(self, proactor: Proactor) -> "CommTestHelper2":
        asyncio.create_task(proactor.run_forever(), name=f"{proactor.name}_run_forever")
        return self

    def start(self) -> "CommTestHelper2":
        return self

    def add_child(self) -> "CommTestHelper2":
        self.child_helper.proactor = self.make_child()
        return self

    def add_parent(self) -> "CommTestHelper2":
        self.parent_helper.proactor = self.make_parent()
        return self

    def remove_child(self) -> "CommTestHelper2":
        self.child_helper.proactor = None
        return self

    def remove_parent(self) -> "CommTestHelper2":
        self.parent_helper.proactor = None
        return self

    def setup_logging(self):
        self.child_helper.settings.paths.mkdirs(parents=True)
        self.parent_helper.settings.paths.mkdirs(parents=True)
        errors = []
        if not self.lifecycle_logging:
            self.child_helper.settings.logging.levels.lifecycle = logging.WARNING
            self.parent_helper.settings.logging.levels.lifecycle = logging.WARNING
        args = argparse.Namespace(verbose=self.verbose)
        self.logger_guards = LoggerGuards()
        setup_logging(args, self.child_helper.settings, errors, add_screen_handler=True, root_gets_handlers=False)
        assert not errors
        setup_logging(args, self.parent_helper.settings, errors,
                      add_screen_handler=self.parent_on_screen, root_gets_handlers=False)
        assert not errors

    async def stop_and_join(self):
        proactors = [
            helper.proactor for helper in [self.child_helper, self.parent_helper]
            if helper.proactor is not None
        ]
        for proactor in proactors:
            # noinspection PyBroadException
            try:
                proactor.stop()
            except:
                pass
        for proactor in proactors:
            # noinspection PyBroadException
            try:
                await proactor.join()
            except:
                pass

    async def __aenter__(self) -> "CommTestHelper2":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop_and_join()
        if exc is not None:
            logging.getLogger("gridworks").error(
                "CommTestHelper caught error %s.\nWorking log dirs:\n\t[%s]\n\t[%s]",
                exc,
                self.child_helper.settings.paths.log_dir,
                self.parent_helper.settings.paths.log_dir,
            )
        self.logger_guards.restore()

