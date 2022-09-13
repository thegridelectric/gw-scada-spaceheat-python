"""Settings for the GridWorks Scada, readable from environment and/or from env files."""
from pathlib import Path
from typing import Optional, Dict

import xdg as xdg
from pydantic import BaseModel, BaseSettings, SecretStr, validator

DEFAULT_ENV_FILE = ".env"


class MQTTClient(BaseModel):
    """Settings for connecting to an MQTT Broker"""
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60
    bind_address: str = ""
    bind_port: int = 0
    username: Optional[str] = None
    password: SecretStr = SecretStr("")

DEFAULT_BASE_DIR = "gridworks"
DEFAULT_NAME_DIR = "scada"
DEFAULT_LAYOUT_FILE = "hardware-layout.json"


class Paths(BaseModel):
    # Relative offsets used under home directories
    base: Path | str   = DEFAULT_BASE_DIR
    name: Path | str   = DEFAULT_NAME_DIR
    relative_path: str | Path   = ""

    # Home directories (defaulting to https://specifications.freedesktop.org/basedir-spec/latest/)
    data_home: Path | str = xdg.XDG_DATA_HOME
    state_home: Path | str = xdg.xdg_state_home()
    config_home: Path | str = xdg.XDG_CONFIG_HOME

    # Base working paths, defaulting home/relative_path/...
    data_dir: str | Path  = ""
    config_dir: str | Path  = ""
    log_dir: str | Path = ""
    hardware_layout: str | Path = ""

    def mkdirs(self, mode: int = 0o777, parents: bool = True, exist_ok: bool = True):
        self.data_dir.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        self.config_dir.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        self.log_dir.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)


    @validator("hardware_layout")
    def get_hardware_layout(cls, v:str|Path, values: Dict[str, Path|str]) -> Path:
        if not v:
            v = values["config_dir"] / DEFAULT_LAYOUT_FILE
        return Path(v)

    @validator("log_dir")
    def get_log_dir(cls, v:str|Path, values: Dict[str, Path|str]) -> Path:
        if not v:
            v = values["state_home"] / values["relative_path"] / "log"
        return Path(v)

    @validator("data_dir")
    def get_data_dir(cls, v:str|Path, values: Dict[str, Path|str]) -> Path:
        if not v:
            v = values["data_home"] / values["relative_path"]
        return Path(v)

    @validator("config_dir")
    def get_config_dir(cls, v:str|Path, values: Dict[str, Path|str]) -> Path:
        if not v:
            v = values["config_home"] / values["relative_path"]
        return Path(v)

    @validator("relative_path")
    def get_relative_path(cls, v:str|Path, values: Dict[str, Path|str]) -> Path:
        if not v:
            v = values["base"] / values["name"]
        return Path(v)



class ScadaSettings(BaseSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    paths: Paths = Paths()
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02
    logging_on: bool = False
    log_message_summary: bool = False


    class Config:
        env_prefix = "SCADA_"
        env_nested_delimiter = "__"
