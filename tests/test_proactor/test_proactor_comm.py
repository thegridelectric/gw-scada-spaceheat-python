# """Test communication issues"""
from gwproactor_test import CommTestHelper
from gwproactor_test.dummies import DummyChild
from gwproactor_test.dummies import DummyChildSettings
from gwproactor_test.dummies import DummyParent
from gwproactor_test.dummies import DummyParentSettings
from gwproactor_test import ProactorCommTests


class DummyCommTestHelper(CommTestHelper):

    parent_t = DummyParent
    child_t = DummyChild
    parent_settings_t = DummyParentSettings
    child_settings_t = DummyChildSettings


class TestDummyProactorComm(ProactorCommTests):
    CTH = DummyCommTestHelper

