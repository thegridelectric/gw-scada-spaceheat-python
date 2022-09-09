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


class TestScadaEnv:
    """Context manager for monkeypatched environment with all vars starting with SCADA_ removed and replaced by
    the contents of the test env file, if specified. Usage:
    >>> os.environ["SCADA_WORLD_ROOT_ALIAS"] = "foo"
    >>> with TestScadaEnv().context() as mpatch:
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
def test_scada_env(request) -> Generator[MonkeyPatch, None, None]:
    """Automatically used fixture producing monkeypatched environment with all vars starting SCADA_ *removed* and then:
        1. Setting SCADA_WORLD_ALIAS_ROOT set to 'dw1'.
        2. Setting variables from the test/.env-gw-spaceheat-test, if present.

    Note that this fixture is run before _every_ test.

    The behavior of this fixture can be customized by:
        1. Modifying the contents of test/.env-gw-spaceheat-test.
        2. Changing the the path to the test dotenv file via the GW_SPACEHEAT_TEST_DOTENV_PATH environment variable.
        3. Explicitly passing and parametrizing this fixture. For example to run the test with SCADA_WORLD_ROOT set to
           "trappist-1e":

                @pytest.mark.parametrize("test_scada_env", [("trappist-1e",)], indirect=True)
                def test_something(test_scada_env):
                    assert os.getenv("SCADA_WORLD_ROOT_ALIAS") == "trappist-1e"
    """
    param = getattr(request, "param", ("dw1", True, "SCADA_"))
    with TestScadaEnv(
        world=param[0] if len(param) > 0 else "dw1",
        use_test_dotenv=param[1] if len(param) > 1 else True,
        prefix=param[2] if len(param) > 2 else "SCADA_"
    ).context() as mpatch:
        yield mpatch


@pytest.fixture
def clean_scada_env(request) -> Generator[MonkeyPatch, None, None]:
    """Get a monkeypatched environment with all vars starting SCADA_ *removed* (and none loaded from any dotenv
    file). """
    param = getattr(request, "param", ("", False, "SCADA_"))
    with TestScadaEnv(
        world=param[0] if len(param) > 0 else "",
        use_test_dotenv=param[1] if len(param) > 1 else False,
        prefix=param[2] if len(param) > 2 else "SCADA_"
    ).context() as mpatch:
        yield mpatch
