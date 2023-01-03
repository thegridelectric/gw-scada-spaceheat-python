from proactor import ProactorSettings
from proactor.config import MQTTClient


class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02

    class Config(ProactorSettings.Config):
        env_prefix = "SCADA_"
