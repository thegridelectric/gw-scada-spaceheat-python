from typing import Any, Optional

from pydantic import validator

from proactor import ProactorSettings
from proactor.config import MQTTClient
from proactor.config import Paths
from proactor.config import LoggingSettings

DEFAULT_NAME = "atn"


class AtnSettings(ProactorSettings):
    scada_mqtt: MQTTClient = MQTTClient()
    minute_cron_file: str = "cron_last_minute.txt"
    hour_cron_file: str = "cron_last_hour.txt"
    day_cron_file: str = "cron_last_day.txt"
    c_to_f: bool = True

    class Config(ProactorSettings.Config):
        env_prefix = "ATN_"

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
