from typing import Callable

from gwproactor.links import StateName

from actors import Scada
from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from tests.atn import Atn
from tests.atn import AtnSettings
from gwproactor_test import CommTestHelper
from gwproactor_test import ProactorTestHelper
from gwproactor_test import RecorderInterface
from gwproactor_test import ProactorCommTests

class RecordedScada(Scada):

    suppress_status: bool = False

    def time_to_send_status(self) -> bool:
        return not self.suppress_status and super().time_to_send_status()

    def disable_derived_events(self) -> None:
        self.suppress_status = True

    def enable_derived_events(self) -> None:
        self.suppress_status = False

    def mqtt_quiescent(self) -> bool:
        return (
            self._links.link(self.GRIDWORKS_MQTT).active_for_send() and
            self._links.link(self.LOCAL_MQTT).state == StateName.awaiting_setup_and_peer
        )


class ScadaCommTestHelper(CommTestHelper):

    parent_t = Atn
    child_t = RecordedScada
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
