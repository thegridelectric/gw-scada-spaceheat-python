from typing import Optional

from pydantic import BaseModel
from pydantic import SecretStr


class MQTTClient(BaseModel):
    """Settings for connecting to an MQTT Broker"""
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60
    bind_address: str = ""
    bind_port: int = 0
    username: Optional[str] = None
    password: SecretStr = SecretStr("")
