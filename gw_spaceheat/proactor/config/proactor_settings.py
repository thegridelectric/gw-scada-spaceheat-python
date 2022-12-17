from pydantic import BaseSettings
from pydantic import validator

from proactor.config.logging import LoggingSettings
from proactor.config.mqtt import MQTTClient
from proactor.config.paths import Paths


class ProactorSettings(BaseSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    paths: Paths = None
    logging: LoggingSettings = LoggingSettings()

    class Config:
        env_prefix = "PROACTOR_"
        env_nested_delimiter = "__"

    @validator("paths", always=True)
    def get_paths(cls, v: Paths) -> Paths:
        if v is None:
            v = Paths()
        return v


