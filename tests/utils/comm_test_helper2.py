import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from typing import Type
from typing import TypeVar

from proactor import ProactorSettings
from logging_setup import setup_logging
from proactor import Proactor

from tests.utils.proactor_dummies import DUMMY_CHILD_NAME
from tests.utils.proactor_dummies import DUMMY_PARENT_NAME
from tests.utils.proactor_dummies import DummyChild
from tests.utils.proactor_dummies import DummyChildSettings
from tests.utils.proactor_dummies import DummyParent
from tests.utils.proactor_dummies import DummyParentSettings
from tests.conftest import LoggerGuards
from tests.utils.proactor_recorder import RecorderInterface
from tests.utils.proactor_recorder import make_recorder_class
from tests.utils.proactor_recorder import ProactorT


@dataclass
class _ProactorHelper:
    name: str
    settings: ProactorSettings
    proactor: Optional[RecorderInterface] = None

ChildT = TypeVar("ChildT", bound=Proactor)
ParentT = TypeVar("ParentT", bound=Proactor)
ChildSettingsT = TypeVar("ChildSettingsT", bound=ProactorSettings)
ParentSettingsT = TypeVar("ParentSettingsT", bound=ProactorSettings)

class CommTestHelper3:

    parent_t: Type[ProactorT]
    child_t: Type[Proactor]
    parent_settings_t: Type[ParentSettingsT]
    child_settings_t: Type[ProactorSettings]

    parent_helper: _ProactorHelper
    child_helper: _ProactorHelper

    verbose: bool
    parent_on_screen: bool
    lifecycle_logging: bool
    logger_guards: LoggerGuards

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
    ):
        self.child_helper = _ProactorHelper(
            self.default_child_name(),
            self.default_child_settings() if child_settings is None else child_settings,
        )
        self.parent_helper = _ProactorHelper(
            self.default_parent_name(),
            self.default_parent_settings() if parent_settings is None else parent_settings,
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
    def default_parent_name(cls) -> str:
        return DUMMY_PARENT_NAME

    @classmethod
    def default_child_name(cls) -> str:
        return DUMMY_CHILD_NAME

    @classmethod
    def default_parent_settings(cls) -> ProactorSettings:
        return cls.parent_settings_t()

    @classmethod
    def default_child_settings(cls) -> ProactorSettings:
        return cls.child_settings_t()

    @classmethod
    def make_parent(cls, name: str, settings: ParentSettingsT) -> RecorderInterface:
        return make_recorder_class(cls.parent_t)(name, settings)

    @classmethod
    def make_child(cls, name: str, settings: ChildSettingsT) -> RecorderInterface:
        return make_recorder_class(cls.child_t)(name, settings)

    @property
    def parent(self) -> Optional[ProactorT]:
        return self.parent_helper.proactor

    @property
    def child(self) -> Optional[ProactorT]:
        return self.child_helper.proactor

    def start_child(self) -> "CommTestHelper3":
        if self.child is not None:
            self.start_proactor(self.child)
        return self

    def start_parent(self) -> "CommTestHelper3":
        if self.parent is not None:
            self.start_proactor(self.parent)
        return self

    def start_proactor(self, proactor: Proactor) -> "CommTestHelper3":
        asyncio.create_task(proactor.run_forever(), name=f"{proactor.name}_run_forever")
        return self

    def start(self) -> "CommTestHelper3":
        return self

    def add_child(self) -> "CommTestHelper3":
        self.child_helper.proactor = self.make_child(
            self.child_helper.name,
            self.child_helper.settings,
        )
        return self

    def add_parent(self) -> "CommTestHelper3":
        self.parent_helper.proactor = self.make_parent(
            self.parent_helper.name,
            self.parent_helper.settings,
        )
        return self

    def remove_child(self) -> "CommTestHelper3":
        self.child_helper.proactor = None
        return self

    def remove_parent(self) -> "CommTestHelper3":
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

    async def __aenter__(self) -> "CommTestHelper3":
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

class CommTestHelper2(CommTestHelper3):

    parent_t = DummyParent
    child_t = DummyChild
    parent_settings_t = DummyParentSettings
    child_settings_t = DummyChildSettings
