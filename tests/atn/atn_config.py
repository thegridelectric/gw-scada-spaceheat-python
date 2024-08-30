from pydantic import model_validator

from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient
from pydantic_settings import SettingsConfigDict

DEFAULT_NAME = "atn"


class AtnSettings(ProactorSettings):
    scada_mqtt: MQTTClient = MQTTClient()
    minute_cron_file: str = "cron_last_minute.txt"
    hour_cron_file: str = "cron_last_hour.txt"
    day_cron_file: str = "cron_last_day.txt"
    c_to_f: bool = True
    save_events: bool = False
    print_status: bool = False
    print_snap: bool = True

    model_config = SettingsConfigDict(env_prefix="ATN_")


    @model_validator(mode="before")
    @classmethod
    def pre_root_validator(cls, values: dict) -> dict:
        return ProactorSettings.update_paths_name(values, DEFAULT_NAME)
