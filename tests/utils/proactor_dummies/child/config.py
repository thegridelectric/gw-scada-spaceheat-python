from proactor import ProactorSettings
from proactor.config import MQTTClient

from tests.utils.proactor_dummies.names import DUMMY_CHILD_ENV_PREFIX


class DummyChildSettings(ProactorSettings):

    parent_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02

    class Config(ProactorSettings.Config):
        env_prefix = DUMMY_CHILD_ENV_PREFIX
