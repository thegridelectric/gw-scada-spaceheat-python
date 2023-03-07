"""Test config module"""
import shutil
import textwrap
from pathlib import Path

import dotenv

from actors.config import PersisterSettings
from gwproactor.config import LoggingSettings
from gwproactor.config import MQTTClient
from gwproactor.config import Paths
from actors.config import ScadaSettings
from pydantic import SecretStr

from gwproactor.config.proactor_settings import MQTT_LINK_POLL_SECONDS


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


def exp_paths_dict(**kwargs) -> dict:
    default_base = Path("gridworks")
    default_name = Path("scada")
    default_relative_path = default_base / default_name
    home = kwargs.pop("home", Path.home())
    default_data_home = home / ".local" / "share"
    default_state_home = home / ".local" / "state"
    default_config_home = home / ".config"
    default_config_dir = default_config_home / default_relative_path
    exp = dict(
        base=default_base,
        name=default_name,
        relative_path=default_relative_path,
        data_home=default_data_home,
        state_home=default_state_home,
        config_home=default_config_home,
        data_dir=default_data_home / default_relative_path,
        config_dir=default_config_dir,
        event_dir=default_data_home / default_relative_path / "event",
        log_dir=default_state_home / default_relative_path / "log",
        hardware_layout=default_config_dir / "hardware-layout.json",
    )
    exp.update(**kwargs)
    return exp


def assert_paths(paths: Paths, **kwargs):
    exp = exp_paths_dict(**kwargs)
    for field, exp_value in exp.items():
        got_value = getattr(paths, field)
        if isinstance(got_value, Path) and not isinstance(exp_value, Path):
            exp_value = Path(exp_value)
            exp[field] = exp_value
        assert got_value == exp_value, f"Paths.{field}\n\texp: {exp_value}\n\tgot: {got_value}"
    assert paths.dict() == exp


def test_paths_defaults(clean_scada_env, tmp_path):
    assert_paths(Paths(), home=tmp_path)


def test_paths(clean_scada_env, tmp_path):
    # base, name
    assert_paths(
        Paths(base="foo", name="bar"),
        home=tmp_path,
        base=Path("foo"),
        name=Path("bar"),
        relative_path=Path("foo/bar"),
        data_dir=tmp_path / ".local/share/foo/bar",
        config_dir=tmp_path / ".config/foo/bar",
        event_dir=tmp_path / ".local/share/foo/bar/event",
        log_dir=tmp_path / ".local/state/foo/bar/log",
        hardware_layout=tmp_path / ".config/foo/bar/hardware-layout.json",
    )

    # explicit relative_path
    assert_paths(
        Paths(relative_path="foo/bar"),
        home=tmp_path,
        relative_path=Path("foo/bar"),
        data_dir=tmp_path / ".local/share/foo/bar",
        config_dir=tmp_path / ".config/foo/bar",
        event_dir=tmp_path / ".local/share/foo/bar/event",
        log_dir=tmp_path / ".local/state/foo/bar/log",
        hardware_layout=tmp_path / ".config/foo/bar/hardware-layout.json",
    )

    # explicit xdg dirs
    assert_paths(
        Paths(data_home="x", state_home="y", config_home="z"),
        home=tmp_path,
        data_home="x",
        state_home="y",
        config_home="z",
        data_dir="x/gridworks/scada",
        event_dir="x/gridworks/scada/event",
        log_dir="y/gridworks/scada/log",
        config_dir="z/gridworks/scada",
        hardware_layout="z/gridworks/scada/hardware-layout.json",
    )

    # explicit working dirs
    assert_paths(
        Paths(data_dir="x", log_dir="y", config_dir="z", event_dir="q"),
        home=tmp_path,
        data_dir="x",
        log_dir="y",
        config_dir="z",
        event_dir="q",
        hardware_layout="z/hardware-layout.json",
    )

    # explicit hardware_layout
    assert_paths(
        Paths(hardware_layout="foo.json"),
        home=tmp_path,
        hardware_layout="foo.json",
    )

    # set xdg through environment
    clean_scada_env.setenv("XDG_DATA_HOME", "/x")
    clean_scada_env.setenv("XDG_STATE_HOME", "/y")
    clean_scada_env.setenv("XDG_CONFIG_HOME", "/z")
    assert_paths(
        Paths(),
        home=tmp_path,
        data_home="/x",
        state_home="/y",
        config_home="/z",
        data_dir="/x/gridworks/scada",
        log_dir="/y/gridworks/scada/log",
        config_dir="/z/gridworks/scada",
        event_dir="/x/gridworks/scada/event",
        hardware_layout="/z/gridworks/scada/hardware-layout.json",
    )


def test_paths_mkdirs(clean_scada_env, tmp_path):
    paths = Paths()
    assert not paths.data_dir.exists()
    # Get rid of the config dir created inside of tmp_path by clean_scada_env
    if paths.config_dir.exists():
        shutil.rmtree(paths.config_dir)
    assert not paths.config_dir.exists()
    assert not paths.log_dir.exists()
    paths.mkdirs()
    assert paths.data_dir.exists()
    assert paths.config_dir.exists()
    assert paths.log_dir.exists()

def test_scada_settings_defaults(clean_scada_env, tmp_path):
    """Test ScadaSettings defaults"""

    # defaults
    settings = ScadaSettings()
    exp = dict(
        local_mqtt=MQTTClient().dict(),
        gridworks_mqtt=MQTTClient().dict(),
        seconds_per_report=300,
        async_power_reporting_threshold=0.02,
        paths=exp_paths_dict(home=tmp_path),
        logging=LoggingSettings().dict(),
        persister=PersisterSettings().dict(),
        mqtt_link_poll_seconds=MQTT_LINK_POLL_SECONDS,
    )
    assert settings.dict() == exp
    assert settings.local_mqtt == MQTTClient()
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
