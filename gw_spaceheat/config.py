"""Settings for the GridWorks Scada, readable from environment and/or from env files."""
from typing import Optional

from pydantic import BaseModel, BaseSettings, SecretStr

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

class ScadaSettings(BaseSettings):
    """Settings for the GridWorks scada."""
    world_root_alias: str
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    output_dir: str = "output"
    seconds_per_report: int = 300
    logging_on: bool = False
    log_message_summary: bool = False

    class Config:
        env_prefix = "SCADA_"
        env_nested_delimiter = "__"
