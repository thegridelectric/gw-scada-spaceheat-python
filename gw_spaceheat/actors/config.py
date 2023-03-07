from pydantic import BaseModel

from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient

DEFAULT_MAX_EVENT_BYTES: int = 500 * 1024 * 1024

class PersisterSettings(BaseModel):
    max_bytes: int = DEFAULT_MAX_EVENT_BYTES

class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02
    persister: PersisterSettings = PersisterSettings()

    class Config(ProactorSettings.Config):
        env_prefix = "SCADA_"
