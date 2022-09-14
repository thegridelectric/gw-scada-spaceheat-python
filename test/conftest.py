"""Local pytest configuration"""

import contextlib
import os
import shutil
from pathlib import Path
from types import NoneType
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch
import dotenv

from config import ScadaSettings, DEFAULT_LAYOUT_FILE, Paths
from test.utils import flush_all

TEST_DOTENV_PATH = "test/.env-gw-spaceheat-test"
TEST_DOTENV_PATH_VAR = "GW_SPACEHEAT_TEST_DOTENV_PATH"
TEST_HARDWARE_LAYOUT_PATH = Path(__file__).parent / "config" / DEFAULT_LAYOUT_FILE
DUMMY_TEST_HARDWARE_LAYOUT_PATH = Path(__file__).parent / "config" / "dummy-hardware-layout.json"

class TestScadaEnv:
    """Context manager for monkeypatched environment with:
        - all vars starting with SCADA_ removed
        - vars loaded from test env file, if specified
        - xdg vars set relative to passed in xdg_home parameter
        - working config directory created via xdg_home
        - test hardware layout file copied into working config directory.

    >>> tmp_path = Path("/home/bla")
    >>> with TestScadaEnv(tmp_path).context() as mpatch:
    ...     assert ScadaSettings().paths.hardware_layout == Path("/home/bla/.config/gridworks/scada/hardware-layout.json")
    ...     assert ScadaSettings().paths.hardware_layout.exists()


    The default test env file is test/.env-gw-spaceheat-test. This path can be overridden with the environment variable
    GW_SPACEHEAT_TEST_DOT_ENV_PATH. The test env file will be ignored if the GW_SPACEHEAT_TEST_DOT_ENV_PATH environment
    variable exists but is empty or the specified path does not exist.

    Hardware file copying can be suppressed by passing copy_test_layout as False.

    Working test directory creation can be suppressed by passing xdg_home as None.
    """

    def __init__(
            self,
            xdg_home: Path | NoneType,
            src_test_layout: Path = TEST_HARDWARE_LAYOUT_PATH,
            copy_test_layout: bool = True,
            use_test_dotenv: bool = True,
            prefix: str = ScadaSettings.Config.env_prefix
    ):
        self.xdg_home = xdg_home
        self.src_test_layout = src_test_layout
        self.copy_test_layout = copy_test_layout
        self.use_test_dotenv = use_test_dotenv
        self.prefix = prefix

    @contextlib.contextmanager
    def context(self) -> Generator[MonkeyPatch, None, None]:
        """Produce monkeypatch context manager from this object"""
        mpatch = MonkeyPatch()
        with mpatch.context() as m:
            self.clean_env(m)
            self.load_test_dotenv()
            self.setup_text_xdg_home(m)
            yield m


    def setup_text_xdg_home(self, m: MonkeyPatch):
        if self.xdg_home is not None:
            m.setenv("XDG_DATA_HOME", str(self.xdg_home / ".local" / "share"))
            m.setenv("XDG_STATE_HOME", str(self.xdg_home / ".local" / "state"))
            m.setenv("XDG_CONFIG_HOME", str(self.xdg_home / ".config"))
            if self.copy_test_layout:
                paths = Paths()
                paths.hardware_layout.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.src_test_layout, paths.hardware_layout)

    def clean_env(self, m: MonkeyPatch):
        if self.use_test_dotenv:
            for env_var in os.environ:
                if env_var.startswith(self.prefix):
                    m.delenv(env_var)

    def load_test_dotenv(self):
        if self.load_test_dotenv:
            test_dotenv_file = os.getenv(TEST_DOTENV_PATH_VAR)
            if test_dotenv_file is None:
                test_dotenv_file = TEST_DOTENV_PATH
            if test_dotenv_file:
                test_dotenv_path = Path(test_dotenv_file)
                if test_dotenv_path.exists():
                    dotenv.load_dotenv(dotenv_path=test_dotenv_path)

@pytest.fixture(autouse=True)
def flush_local_registries():
    flush_all()

@pytest.fixture(autouse=True)
def test_scada_env(request, tmp_path) -> Generator[MonkeyPatch, None, None]:
    """Automatically used fixture producing monkeypatched environment with:
        - all vars starting with SCADA_ removed
        - vars loaded from test env file, if specified
        - xdg vars set relative to passed in xdg_home parameter
        - working config directory created via xdg_home
        - test hardware layout file copied into working config directory.

    Note that this fixture is run before _every_ test.

    The behavior of this fixture can be customized by:
        1. Modifying the contents of test/.env-gw-spaceheat-test.
        2. Changing the the path to the test dotenv file via the GW_SPACEHEAT_TEST_DOTENV_PATH environment variable.
        3. Explicitly passing and parametrizing this fixture. For example, to run a test with a different hardware
          layout file, such as DUMMY_TEST_HARDWARE_LAYOUT_PATH:

            >>> from test.conftest import DUMMY_TEST_HARDWARE_LAYOUT_PATH
            >>> @pytest.mark.parametrize("test_scada_env", [("",DUMMY_TEST_HARDWARE_LAYOUT_PATH)], indirect=True)
            >>> def test_something(test_scada_env):
            >>>    assert Paths().hardware_layout.open().read() == DUMMY_TEST_HARDWARE_LAYOUT_PATH.open().read()

    """
    param = getattr(request, "param", (tmp_path, TEST_HARDWARE_LAYOUT_PATH, True, True, "SCADA_"))
    if len(param) > 0:
        xdg_home = param[0]
        if xdg_home == "":
            xdg_home = tmp_path
    else:
        xdg_home = tmp_path
    with TestScadaEnv(
        xdg_home=xdg_home,
        src_test_layout=param[1] if len(param) > 1 else TEST_HARDWARE_LAYOUT_PATH,
        copy_test_layout=param[2] if len(param) > 2 else True,
        use_test_dotenv=param[3] if len(param) > 3 else True,
        prefix=param[4] if len(param) > 4 else "SCADA_"
    ).context() as mpatch:
        yield mpatch


@pytest.fixture
def clean_scada_env(request, tmp_path) -> Generator[MonkeyPatch, None, None]:
    """Get a monkeypatched environment with all vars starting SCADA_ *removed* (and none loaded from any dotenv
    file). """
    param = getattr(request, "param", (tmp_path, TEST_HARDWARE_LAYOUT_PATH, True, False, "SCADA_"))
    if len(param) > 0:
        xdg_home = param[0]
        if xdg_home == "":
            xdg_home = tmp_path
    else:
        xdg_home = tmp_path
    with TestScadaEnv(
        xdg_home=xdg_home,
        src_test_layout=param[1] if len(param) > 1 else TEST_HARDWARE_LAYOUT_PATH,
        copy_test_layout=param[2] if len(param) > 2 else True,
        use_test_dotenv=param[3] if len(param) > 3 else False,
        prefix=param[4] if len(param) > 4 else "SCADA_"
    ).context() as mpatch:
        yield mpatch
