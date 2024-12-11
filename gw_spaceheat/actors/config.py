from gwproactor.config.mqtt import TLSInfo
from pydantic import model_validator, BaseModel
from data_classes.house_0_names import H0N
from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient
from pydantic_settings import SettingsConfigDict

DEFAULT_MAX_EVENT_BYTES: int = 500 * 1024 * 1024

class PersisterSettings(BaseModel):
    max_bytes: int = DEFAULT_MAX_EVENT_BYTES


class AdminLinkSettings(MQTTClient):
    enabled: bool = False
    name: str = H0N.admin
    timeout_seconds: float = 60 * 1

class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    local_mqtt: MQTTClient = MQTTClient()
    gridworks_mqtt: MQTTClient = MQTTClient()
    seconds_per_report: int = 300
    seconds_per_snapshot: int = 30
    async_power_reporting_threshold: float = 0.02
    persister: PersisterSettings = PersisterSettings()
    admin: AdminLinkSettings = AdminLinkSettings()
    timezone_str: str = "America/New_York"
    latitude: float = 45.6573 
    longitude: float = -68.7098
    alpha: float = 5.5
    beta: float = -0.1
    gamma: float = 0
    hp_max_kw_th: float = 14
    intermediate_power: float = 1.5
    intermediate_rswt: float = 100
    dd_power: float = 5.5
    dd_rswt: float = 150
    dd_delta_t: float = 20
    is_simulated: bool = False
    max_ewt_f: int = 170

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
