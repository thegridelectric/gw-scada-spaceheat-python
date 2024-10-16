import re

from pydantic import BaseModel
from pydantic import model_validator

from gwproactor import ProactorSettings
from gwproactor.config import MQTTClient
from pydantic_settings import SettingsConfigDict

DEFAULT_NAME = "atn"

class HackHpSettings(BaseModel):
    ops_genie_api_key: str = ""
    gridworks_team_id: str = ""
    moscone_team_id: str = ""

class DashboardSettings(BaseModel):
    print_report: bool = True
    print_snap: bool = True
    print_gui: bool = False
    print_hack_hp: bool = False
    print_thermostat_history: bool = False
    raise_dashboard_exceptions: bool = False
    hack_hp: HackHpSettings = HackHpSettings()

    @classmethod
    def thermostat_names(cls, channel_names: list[str]) -> list[str]:
        thermostat_channel_name_pattern = re.compile(
            r"^zone(?P<zone_number>\d)-(?P<human_name>.*)-(temp|set|state)$"
        )
        thermostat_human_names = []
        for channel_name in channel_names:
            if match := thermostat_channel_name_pattern.match(channel_name):
                if (human_name := match.group("human_name")) not in thermostat_human_names:
                    thermostat_human_names.append(human_name)
        return thermostat_human_names

class AtnSettings(ProactorSettings):
    scada_mqtt: MQTTClient = MQTTClient()
    c_to_f: bool = True
    save_events: bool = False
    dashboard: DashboardSettings = DashboardSettings()

    model_config = SettingsConfigDict(env_prefix="ATN_", extra="ignore")


    @model_validator(mode="before")
    @classmethod
    def pre_root_validator(cls, values: dict) -> dict:
        return ProactorSettings.update_paths_name(values, DEFAULT_NAME)

