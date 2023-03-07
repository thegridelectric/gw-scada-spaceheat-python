# """Test communication issues"""
from tests.utils.comm_test_helper import CommTestHelper
from tests.utils.proactor_dummies import DummyChild
from tests.utils.proactor_dummies import DummyChildSettings
from tests.utils.proactor_dummies import DummyParent
from tests.utils.proactor_dummies import DummyParentSettings
from tests.utils.proactor_test_collections import ProactorCommTests


class DummyCommTestHelper(CommTestHelper):

    parent_t = DummyParent
    child_t = DummyChild
    parent_settings_t = DummyParentSettings
    child_settings_t = DummyChildSettings


class TestDummyProactorComm(ProactorCommTests):
    CTH = DummyCommTestHelper

