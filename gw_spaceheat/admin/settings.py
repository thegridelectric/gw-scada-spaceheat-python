import logging
from typing import Self

from gwproactor.config import MQTTClient
from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from gwproactor import ProactorSettings
from data_classes.house_0_names import H0N


class AdminClientSettings(ProactorSettings):
    target_gnode: str = ""
    link: MQTTClient = MQTTClient()
    verbosity: int = logging.WARN
    model_config = SettingsConfigDict(
        env_prefix="GWADMIN_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @model_validator(mode="before")
    @classmethod
    def pre_root_validator(cls, values: dict) -> dict:
        return ProactorSettings.update_paths_name(values, H0N.admin)

    @model_validator(mode="after")
    def validate(self) -> Self:
        self.link.update_tls_paths(self.paths.certs_dir, H0N.admin)
        return self
