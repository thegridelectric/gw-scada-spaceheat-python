
import pytest

from gwproactor_test import ProactorCommTests

from tests.utils.scada_comm_test_helper import ScadaCommTestHelper


@pytest.mark.skip(reason="Comm tests are too flaky with scada")
class TestScadaProactorComm(ProactorCommTests):
    CTH = ScadaCommTestHelper
