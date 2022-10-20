from pydantic import BaseSettings, validator

from .mqtt import MQTTClient
from .paths import Paths
from .logging import LoggingSettings

class ScadaSettings(BaseSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    paths: Paths = None
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02
    logging: LoggingSettings = LoggingSettings()

    class Config:
        env_prefix = "SCADA_"
        env_nested_delimiter = "__"

    @validator("paths", always=True)
    def get_paths(cls, v: Paths) -> Paths:
        if v is None:
            v = Paths()
        return v
