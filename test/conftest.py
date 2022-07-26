"""Local pytest configuration"""

import contextlib
import os
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from config import ScadaSettings
from test.utils import flush_all


class CleanScadaEnv:
    """Context manager for monkeypatched environment with all vars starting with SCADA_ removed. Usage:
    >>> os.environ["SCADA_WORLD_ROOT_ALIAS"] = "foo"
    >>> with CleanScadaEnv().context() as mpatch:
    ...     assert os.getenv("SCADA_WORLD_ROOT_ALIAS") == "dwtest"
    """

    def __init__(self, world: str = "dwtest", prefix: str = ScadaSettings.Config.env_prefix):
        self.world = world
        self.prefix = prefix

    @contextlib.contextmanager
    def context(self) -> Generator[MonkeyPatch, None, None]:
        """"""
        mpatch = MonkeyPatch()
        with mpatch.context() as m:
            for env_var in os.environ:
                if env_var.startswith(self.prefix):
                    m.delenv(env_var)
            if self.world:
                m.setenv(f"{self.prefix}WORLD_ROOT_ALIAS", self.world)
            yield m


@pytest.fixture(autouse=True)
def flush_local_registries():
    flush_all()


@pytest.fixture(autouse=True)
def clean_scada_env(request) -> Generator[MonkeyPatch, None, None]:
    """Automatically used fixture producing monkeypatched environment with all vars starting SCADA_ removed and then
    setting enviroment variable to SCADA_WORLD_ALIAS_ROOT set to 'dwtest'.

    Note that this fixture is run before _every_ test.

    To customize the behavior of this fixture pass it explicitly to a test and parametrize it. For example to run the
    test with SCADA_WORLD_ROOT set to "trappist-1e":

        @pytest.mark.parametrize("clean_scada_env", [("trappist-1e",)], indirect=True)
        def test_something(clean_scada_env):
            assert os.getenv("SCADA_WORLD_ROOT_ALIAS") == "trappist-1e"
    """
    param = getattr(request, "param", ("dwtest", "SCADA_"))
    with CleanScadaEnv(
        world=param[0] if len(param) > 0 else "dwtest",
        prefix=param[1] if len(param) > 1 else "SCADA_"
    ).context() as mpatch:
        yield mpatch
