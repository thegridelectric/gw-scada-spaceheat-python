"""Local pytest configuration"""

import contextlib
import os
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch
import dotenv

from config import ScadaSettings
from test.utils import flush_all

TEST_DOTENV_PATH = "test/.env-gw-spaceheat-test"
TEST_DOTENV_PATH_VAR = "GW_SPACEHEAT_TEST_DOTENV_PATH"


class CleanScadaEnv:
    """Context manager for monkeypatched environment with all vars starting with SCADA_ removed and replaced by
    the contents of the test env file, if specified. Usage:
    >>> os.environ["SCADA_WORLD_ROOT_ALIAS"] = "foo"
    >>> with CleanScadaEnv().context() as mpatch:
    ...     assert os.getenv("SCADA_WORLD_ROOT_ALIAS") == "dw1"

    The default test env file is test/.env-gw-spaceheat-test. This path can be overridden with the environment variable
    GW_SPACEHEAT_TEST_DOT_ENV_PATH. The test env file will be ignored if the GW_SPACEHEAT_TEST_DOT_ENV_PATH environment
    variable exists but is empty or the specified path does not exist.
    """

    def __init__(self, world: str = "dw1", use_test_dotenv: bool = True, prefix: str = ScadaSettings.Config.env_prefix):
        self.world = world
        self.use_test_dotenv = use_test_dotenv
        self.prefix = prefix

    @contextlib.contextmanager
    def context(self) -> Generator[MonkeyPatch, None, None]:
        """Produce monkeypatch context manager from this object"""
        mpatch = MonkeyPatch()
        with mpatch.context() as m:
            for env_var in os.environ:
                if env_var.startswith(self.prefix):
                    m.delenv(env_var)
            if self.world:
                m.setenv(f"{self.prefix}WORLD_ROOT_ALIAS", self.world)
            if self.use_test_dotenv:
                test_dotenv_file = os.getenv(TEST_DOTENV_PATH_VAR)
                if test_dotenv_file is None:
                    test_dotenv_file = TEST_DOTENV_PATH
                if test_dotenv_file:
                    test_dotenv_path = Path(test_dotenv_file)
                    if test_dotenv_path.exists():
                        dotenv.load_dotenv(dotenv_path=test_dotenv_path)
            yield m


@pytest.fixture(autouse=True)
def flush_local_registries():
    flush_all()


@pytest.fixture(autouse=True)
def clean_scada_env(request) -> Generator[MonkeyPatch, None, None]:
    """Automatically used fixture producing monkeypatched environment with all vars starting SCADA_ removed and then
    setting enviroment variable to SCADA_WORLD_ALIAS_ROOT set to 'dw1'. If the test dotenv file
    (.test/.env-gw-spaceheat-test or the value of the environment variable TEST_DOTENV_PATH_VAR) exists, its contents
    will be used to set the environment after cleaning previously existing SCDADA_ vars.

    Note that this fixture is run before _every_ test.

    To customize the behavior of this fixture use the test dotenv file as described above or pass the fixture explicitly
    to a test and parametrize it. For example to run the test with SCADA_WORLD_ROOT set to "trappist-1e":

        @pytest.mark.parametrize("clean_scada_env", [("trappist-1e",)], indirect=True)
        def test_something(clean_scada_env):
            assert os.getenv("SCADA_WORLD_ROOT_ALIAS") == "trappist-1e"


    """
    param = getattr(request, "param", ("dw1", True, "SCADA_"))
    with CleanScadaEnv(
        world=param[0] if len(param) > 0 else "dw1",
        use_test_dotenv=param[1] if len(param) > 1 else True,
        prefix=param[2] if len(param) > 2 else "SCADA_"
    ).context() as mpatch:
        yield mpatch
