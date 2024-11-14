from gwproactor.config.mqtt import TLSInfo
from pydantic import model_validator, BaseModel
from gwproto.data_classes.house_0_names import H0N
from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient
from pydantic_settings import SettingsConfigDict

DEFAULT_MAX_EVENT_BYTES: int = 500 * 1024 * 1024

class PersisterSettings(BaseModel):
    max_bytes: int = DEFAULT_MAX_EVENT_BYTES


class AdminLinkSettings(MQTTClient):
    enabled: bool = False
    name: str = H0N.admin

class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    async_power_reporting_threshold: float = 0.02
    persister: PersisterSettings = PersisterSettings()
    admin: AdminLinkSettings = AdminLinkSettings()
    swt_coldest_hour: int = 120
    average_power_coldest_hour_kw: float = 4
    buffer_empty: int = 110
    buffer_full: int = 125


    model_config = SettingsConfigDict(env_prefix="SCADA_", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def pre_root_validator(cls, values: dict) -> dict:
        """local_mqtt configuration should be without TLS unless explicitly requested."""
        if "local_mqtt" not in values:
            values["local_mqtt"] = MQTTClient(tls=TLSInfo(use_tls=False))
        elif "tls" not in values["local_mqtt"]:
            values["local_mqtt"]["tls"] = TLSInfo(use_tls=False)
        elif "use_tls" not in values["local_mqtt"]["tls"]:
            values["local_mqtt"]["tls"]["use_tls"] = False
        return values
