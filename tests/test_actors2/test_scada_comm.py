from typing import Callable

from actors2 import Scada2
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from tests.atn import Atn2
from tests.atn import AtnSettings
from tests.utils.comm_test_helper import CommTestHelper
from tests.utils.comm_test_helper import ProactorTestHelper
from tests.utils.proactor_recorder import RecorderInterface
from tests.utils.proactor_test_collections import ProactorCommTests


class ScadaCommTestHelper(CommTestHelper):

    parent_t = Atn2
    child_t = Scada2
    parent_settings_t = AtnSettings
    child_settings_t = ScadaSettings

    @classmethod
    def _make(cls, recorder_t: Callable[..., RecorderInterface], helper: ProactorTestHelper) -> RecorderInterface:
        if "hardware_layout" not in helper.kwargs:
            helper.kwargs["hardware_layout"] = HardwareLayout.load(helper.settings.paths.hardware_layout)
        return super()._make(recorder_t, helper)


class TestScadaProactorComm(ProactorCommTests):
    CTH = ScadaCommTestHelper

    async def test_ping2(self):
        await super().test_ping2()
