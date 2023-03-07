from pydantic import BaseSettings
from pydantic import validator

from gwproactor.config.logging import LoggingSettings
from gwproactor.config.paths import Paths

MQTT_LINK_POLL_SECONDS = 60

class ProactorSettings(BaseSettings):
    paths: Paths = None
    logging: LoggingSettings = LoggingSettings()
    mqtt_link_poll_seconds: float = MQTT_LINK_POLL_SECONDS

    class Config:
        env_prefix = "PROACTOR_"
        env_nested_delimiter = "__"

    @validator("paths", always=True)
    def get_paths(cls, v: Paths) -> Paths:
        if v is None:
            v = Paths()
        return v


