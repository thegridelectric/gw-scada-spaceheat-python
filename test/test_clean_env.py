import json
from test.conftest import DUMMY_TEST_HARDWARE_LAYOUT_PATH

import pytest
from config import Paths
from data_classes.hardware_layout import HardwareLayout


def test_clean_env(tmp_path):
    exp_data_home = tmp_path / ".local" / "share"
    exp_state_home = tmp_path / ".local" / "state"
    exp_config_home = tmp_path / ".config"
    paths = Paths()
    assert paths.data_home == exp_data_home
    assert paths.state_home == exp_state_home
    assert paths.config_home == exp_config_home
    assert paths.hardware_layout.exists()
    HardwareLayout.load(paths.hardware_layout)


@pytest.mark.parametrize("test_scada_env", [("", DUMMY_TEST_HARDWARE_LAYOUT_PATH)], indirect=True)
def test_custom_hardware_layout_file(test_scada_env):
    paths = Paths()
    assert paths.hardware_layout.exists()
    assert paths.hardware_layout.open().read() == DUMMY_TEST_HARDWARE_LAYOUT_PATH.open().read()
