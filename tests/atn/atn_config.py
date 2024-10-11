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
    raise_dashboard_exceptions: bool = False
    hack_hp: HackHpSettings = HackHpSettings()

    @classmethod
    def thermostat_names(cls, node_names: list[str]) -> list[str]:
        name_to_human_name :dict[str, str] = {}
        thermostat_name_pattern = re.compile(
            "^zone(?P<zone_number>\d)-(?P<human_name>.*)$"
        )
        for node_name in node_names:
            if match := thermostat_name_pattern.match(node_name):
                name_to_human_name[node_name] = match.group("human_name")
        return [
            name_to_human_name[name] for name in sorted(name_to_human_name.keys())
        ]

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

