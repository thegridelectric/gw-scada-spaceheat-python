from typing import Callable

from actors import Scada
from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from tests.atn import Atn
from tests.atn import AtnSettings
from gwproactor_test import CommTestHelper
from gwproactor_test import ProactorTestHelper
from gwproactor_test import RecorderInterface
from gwproactor_test import ProactorCommTests


class ScadaCommTestHelper(CommTestHelper):

    parent_t = Atn
    child_t = Scada
    parent_settings_t = AtnSettings
    child_settings_t = ScadaSettings
    warn_if_multi_subscription_tests_skipped: bool = False

    def __init__(self, **kwargs):
        super().__init__(**dict(child_path_name="scada", parent_path_name="atn", **kwargs))

    @classmethod
    def _make(cls, recorder_t: Callable[..., RecorderInterface], helper: ProactorTestHelper) -> RecorderInterface:
        if "hardware_layout" not in helper.kwargs:
            helper.kwargs["hardware_layout"] = HardwareLayout.load(helper.settings.paths.hardware_layout)
        return super()._make(recorder_t, helper)

class TestScadaProactorComm(ProactorCommTests):
    CTH = ScadaCommTestHelper
