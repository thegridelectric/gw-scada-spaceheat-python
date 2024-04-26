from pydantic import root_validator

from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient

DEFAULT_NAME = "atn"


class AtnSettings(ProactorSettings):
    scada_mqtt: MQTTClient = MQTTClient()
    minute_cron_file: str = "cron_last_minute.txt"
    hour_cron_file: str = "cron_last_hour.txt"
    day_cron_file: str = "cron_last_day.txt"
    c_to_f: bool = True
    save_events: bool = False
    print_status: bool = False
    ops_genie_api_key: str = ""

    class Config(ProactorSettings.Config):
        env_prefix = "ATN_"

    @root_validator(pre=True)
    def pre_root_validator(cls, values: dict) -> dict:
        return ProactorSettings.update_paths_name(values, DEFAULT_NAME)
