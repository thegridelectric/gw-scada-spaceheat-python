from gwproactor.config.mqtt import TLSInfo
from pydantic import BaseModel

from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient
from pydantic import root_validator

DEFAULT_MAX_EVENT_BYTES: int = 500 * 1024 * 1024

class PersisterSettings(BaseModel):
    max_bytes: int = DEFAULT_MAX_EVENT_BYTES

class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02
    persister: PersisterSettings = PersisterSettings()

    class Config(ProactorSettings.Config):
        env_prefix = "SCADA_"

    @root_validator(pre=True)
    def pre_root_validator(cls, values: dict) -> dict:
        """local_mqtt configuration should be without TLS unless explicitly requested."""
        if "local_mqtt" not in values:
            values["local_mqtt"] = MQTTClient(tls=TLSInfo(use_tls=False))
        elif "tls" not in values["local_mqtt"]:
            values["local_mqtt"]["tls"] = TLSInfo(use_tls=False)
        elif "use_tls" not in values["local_mqtt"]["tls"]:
            values["local_mqtt"]["tls"]["use_tls"] = False
        return values
