"""Test config module"""
import os
import textwrap
from pathlib import Path

import dotenv
import pydantic
import pytest
from pydantic import SecretStr

from config import MQTTClient, ScadaSettings


def test_mqtt_client_settings():
    """Test MQTTClient"""
    password = "d"
    port = 1883
    exp = dict(host="a", keepalive=1, bind_address="b", bind_port=2, username="c", password=SecretStr(password))
    settings = MQTTClient(**exp)
    d = settings.dict()
    assert d == dict(exp, port=port)
    for k, v in exp.items():
        assert d[k] == v
        assert getattr(settings, k) == v
    assert settings.port == port
    assert settings.password.get_secret_value() == password


@pytest.mark.parametrize("clean_scada_env", [("",)], indirect=True)
def test_scada_settings_defaults(clean_scada_env):
    """Test ScadaSettings defaults"""

    # world_root_alias required
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        ScadaSettings()

    # defaults
    settings = ScadaSettings(world_root_alias="foo")
    exp = dict(
        world_root_alias="foo",
        output_dir="output",
        local_mqtt=MQTTClient().dict(),
        gridworks_mqtt=MQTTClient().dict(),
        seconds_per_report=300,
        async_power_reporting_threshold=0.02,
        logging_on=False,
        log_message_summary=False,
    )
    assert settings.world_root_alias == "foo"
    assert settings.dict() == exp
    assert settings.local_mqtt == MQTTClient()
    assert settings.local_mqtt.username is None
    assert settings.local_mqtt.password.get_secret_value() == ""


def test_scada_settings_from_env(monkeypatch):
    """Verify settings loaded from env as expected. """
    monkeypatch.delenv("SCADA_WORLD_ROOT_ALIAS")
    assert "SCADA_WORLD_ROOT_ALIAS" not in os.environ
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        ScadaSettings()
    world = "Foo"
    monkeypatch.setenv("SCADA_WORLD_ROOT_ALIAS", world)
    settings = ScadaSettings()
    assert settings.world_root_alias == world
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


def test_scada_settings_from_dotenv(monkeypatch, tmp_path):
    """Verify settings loaded from .env file as expected. """
    monkeypatch.delenv("SCADA_WORLD_ROOT_ALIAS")
    env_file = Path(tmp_path) / ".env"
    settings = ScadaSettings(world_root_alias="1", _env_file=env_file)
    assert settings.seconds_per_report == 300
    assert settings.local_mqtt.host == "localhost"
    assert settings.local_mqtt.password.get_secret_value() == ""
    world = "Foo"
    seconds_per_report = 1
    host = "x"
    password = "y"
    with env_file.open("w") as f:
        f.write(
            textwrap.dedent(
                f"""
                SCADA_WORLD_ROOT_ALIAS="{world}"
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
    assert settings.world_root_alias == world
    assert settings.seconds_per_report == seconds_per_report
    assert settings.local_mqtt.host == host
    assert settings.local_mqtt.password.get_secret_value() == password


def test_scada_settings_from_env_and_dotenv(monkeypatch, tmp_path):
    """Verify settings loaded from both environment variables and .env and as expected - environment variables
    take precedence"""
    env = dict(
        SCADA_WORLD_ROOT_ALIAS="a",
        SCADA_LOCAL_MQTT__PASSWORD="1"
    )
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    dotenv_ = dict(
        SCADA_WORLD_ROOT_ALIAS="b",
        SCADA_GRIDWORKS_MQTT__PASSWORD="2"
    )
    env_file = Path(tmp_path) / ".env"
    with env_file.open("w") as f:
        for k, v in dotenv_.items():
            f.write(f"{k}={v}\n")
    settings = ScadaSettings(_env_file=env_file)
    assert settings.world_root_alias == env["SCADA_WORLD_ROOT_ALIAS"]
    assert settings.local_mqtt.password.get_secret_value() == env["SCADA_LOCAL_MQTT__PASSWORD"]
    assert settings.gridworks_mqtt.password.get_secret_value() == dotenv_["SCADA_GRIDWORKS_MQTT__PASSWORD"]
