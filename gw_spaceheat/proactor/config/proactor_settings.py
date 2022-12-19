from pydantic import BaseSettings
from pydantic import validator

from proactor.config.logging import LoggingSettings
from proactor.config.paths import Paths


class ProactorSettings(BaseSettings):
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


