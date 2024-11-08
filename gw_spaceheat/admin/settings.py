from typing import Self

from gwproactor.config import MQTTClient
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from gwproactor import ProactorSettings
from gwproactor.config import Paths

from actors.config import ADMIN_NAME


class AdminClientSettings(ProactorSettings):
    target_gnode: str = ""
    paths: Paths = Field({}, validate_default=True)
    link: MQTTClient = MQTTClient()
    model_config = SettingsConfigDict(env_prefix="GWADMIN_", env_nested_delimiter="__")

    @model_validator(mode="before")
    @classmethod
    def pre_root_validator(cls, values: dict) -> dict:
        return ProactorSettings.update_paths_name(values, ADMIN_NAME)

    @model_validator(mode="after")
    def validate(self) -> Self:
        self.link.update_tls_paths(self.paths.certs_dir, ADMIN_NAME)
        return self
