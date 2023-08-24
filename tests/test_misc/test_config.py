"""Test config module"""
import textwrap
from pathlib import Path

import dotenv
from gwproactor.config import Paths
from gwproactor.config.mqtt import TLSInfo
from gwproactor.config.proactor_settings import ACK_TIMEOUT_SECONDS
from gwproactor.config.proactor_settings import NUM_INITIAL_EVENT_REUPLOADS

from actors.config import PersisterSettings
from gwproactor.config import LoggingSettings
from gwproactor.config import MQTTClient
from actors.config import ScadaSettings

from gwproactor.config.proactor_settings import MQTT_LINK_POLL_SECONDS


def test_scada_settings_defaults(clean_scada_env):
    """Test ScadaSettings defaults"""

    # defaults
    settings = ScadaSettings()
    exp_local_mqtt = MQTTClient(
        tls=TLSInfo(
            use_tls=False
        ).update_tls_paths(
            Paths().certs_dir,
            "local_mqtt"
        )
    )
    exp = dict(
        local_mqtt=exp_local_mqtt.dict(),
        gridworks_mqtt=MQTTClient(
            tls=TLSInfo().update_tls_paths(
                Paths().certs_dir,
                "gridworks_mqtt"
            )
        ).dict(),
        seconds_per_report=300,
        async_power_reporting_threshold=0.02,
        paths=Paths().dict(),
        logging=LoggingSettings().dict(),
        persister=PersisterSettings().dict(),
        mqtt_link_poll_seconds=MQTT_LINK_POLL_SECONDS,
        ack_timeout_seconds=ACK_TIMEOUT_SECONDS,
        num_initial_event_reuploads=NUM_INITIAL_EVENT_REUPLOADS,
    )
    assert settings.dict() == exp
    assert settings.local_mqtt == exp_local_mqtt
    assert settings.local_mqtt.username is None
    assert settings.local_mqtt.password.get_secret_value() == ""


def test_scada_settings_from_env(monkeypatch, clean_scada_env):
    """Verify settings loaded from env as expected. """
    settings = ScadaSettings()
    assert settings.seconds_per_report == 300
    assert settings.local_mqtt.host == "localhost"
    assert settings.local_mqtt.password.get_secret_value() == ""
    assert settings.gridworks_mqtt.host == "localhost"
    assert settings.gridworks_mqtt.password.get_secret_value() == ""
    exp = dict(
        SCADA_SECONDS_PER_REPORT="1",
        SCADA_LOCAL_MQTT__HOST="foo",
        SCADA_LOCAL_MQTT__PASSWORD="a",
        SCADA_GRIDWORKS_MQTT__HOST="b",
        SCADA_GRIDWORKS_MQTT__PASSWORD="c",
    )
    for k, v in exp.items():
        monkeypatch.setenv(k, v)
    settings = ScadaSettings()
    assert settings.seconds_per_report == int(exp["SCADA_SECONDS_PER_REPORT"])
    assert settings.local_mqtt.host == exp["SCADA_LOCAL_MQTT__HOST"]
    assert settings.local_mqtt.password.get_secret_value() == exp["SCADA_LOCAL_MQTT__PASSWORD"]
    assert settings.gridworks_mqtt.host == exp["SCADA_GRIDWORKS_MQTT__HOST"]
    assert settings.gridworks_mqtt.password.get_secret_value() == exp["SCADA_GRIDWORKS_MQTT__PASSWORD"]


def test_scada_settings_from_dotenv(monkeypatch, tmp_path, clean_scada_env):
    """Verify settings loaded from .env file as expected. """
    env_file = Path(tmp_path) / ".env"
    settings = ScadaSettings(_env_file=env_file)
    assert settings.seconds_per_report == 300
    assert settings.local_mqtt.host == "localhost"
    assert settings.local_mqtt.password.get_secret_value() == ""
    seconds_per_report = 1
    host = "x"
    password = "y"
    with env_file.open("w") as f:
        f.write(
            textwrap.dedent(
                f"""
                SCADA_SECONDS_PER_REPORT={seconds_per_report}
                SCADA_LOCAL_MQTT__HOST={host}
                SCADA_LOCAL_MQTT__PASSWORD={password}
                """
            )
        )
    working_dir = tmp_path / "foo/bar"
    working_dir.mkdir(parents=True)
    monkeypatch.chdir(working_dir)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(str(env_file)))
    assert settings.seconds_per_report == seconds_per_report
    assert settings.local_mqtt.host == host
    assert settings.local_mqtt.password.get_secret_value() == password


def test_scada_settings_from_env_and_dotenv(monkeypatch, tmp_path, clean_scada_env):
    """Verify settings loaded from both environment variables and .env and as expected - environment variables
    take precedence"""
    env = dict(
        SCADA_LOCAL_MQTT__PASSWORD="1"
    )
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    dotenv_ = dict(
        SCADA_GRIDWORKS_MQTT__PASSWORD="2"
    )
    env_file = Path(tmp_path) / ".env"
    with env_file.open("w") as f:
        for k, v in dotenv_.items():
            f.write(f"{k}={v}\n")
    settings = ScadaSettings(_env_file=env_file)
    assert settings.local_mqtt.password.get_secret_value() == env["SCADA_LOCAL_MQTT__PASSWORD"]
    assert settings.gridworks_mqtt.password.get_secret_value() == dotenv_["SCADA_GRIDWORKS_MQTT__PASSWORD"]
