from typing import Optional, Any

from pydantic import BaseSettings, validator

from config import MQTTClient
from config import Paths
from config import LoggingSettings

DEFAULT_NAME = "atn"


class AtnSettings(BaseSettings):
    scada_mqtt: MQTTClient = MQTTClient()
    paths: Paths = None
    logging: LoggingSettings = None

    class Config:
        env_prefix = "ATN_"
        env_nested_delimiter = "__"

    @validator("paths", always=True)
    def get_paths(cls, v: Optional[Paths]) -> Paths:
        if v is None:
            v = Paths(name=DEFAULT_NAME)
        return v

    @validator("logging", always=True)
    def get_logging(cls, v: Optional[LoggingSettings], values: dict[str, Any]) -> LoggingSettings:
        if v is None:
            v = LoggingSettings()
        if not isinstance(values["paths"], Paths):
            raise ValueError(f"ERROR. 'paths' value has type {type(values['paths'])}, not Paths")
        paths: Paths = values["paths"]
        v.base_log_name = str(paths.name)
        v.file_handler.filename = "atn.log"
        return v
