import json
from typer.testing import CliRunner

import cli as gws
from actors.config import ScadaSettings

runner = CliRunner()

def test_gws():
    result = runner.invoke(gws.app)
    assert result.exit_code == 0
    assert gws.app.info.help in result.output

def test_gws_version():
    result = runner.invoke(gws.app, ["--version"])
    assert result.exit_code == 0
    assert gws.__version__ in result.output

def test_gws_config(tmp_path, monkeypatch):
    """Verify 'gws config' runs, loads from env file and produces json output"""

    monkeypatch.chdir(tmp_path)
    exp_host = "foo"
    env_path = tmp_path / ".foo-env"
    with env_path.open("w") as env_file:
        env_file.write(f'SCADA_GRIDWORKS_MQTT__HOST="{exp_host}"')

    # with env file
    result = runner.invoke(gws.app, ["config", "--env-file", env_path])
    assert result.exit_code == 0
    assert exp_host in result.output

    # as json
    result = runner.invoke(gws.app, ["config", "--env-file", env_path, "--json"])
    assert result.exit_code == 0
    loaded = json.loads(result.output)
    assert loaded["env_file"] == str(env_path)
    assert loaded["env_file_exists"]
    settings = ScadaSettings.model_validate(loaded["config"])
    assert settings.gridworks_mqtt.host == exp_host

    # missing env file
    result = runner.invoke(gws.app, ["config", "--env-file", str(env_path) + "X", "--json"])
    assert result.exit_code == 0
    loaded = json.loads(result.output)
    assert not loaded["env_file_exists"]
    settings = ScadaSettings.model_validate(loaded["config"])
    assert settings.gridworks_mqtt.host == "localhost"

def test_gws_layout_show():
    """Test that 'gws layout show' runs and produces some expected output"""
    result = runner.invoke(gws.app, ["layout", "show"])
    assert result.exit_code == 0
    # simple test that a tiny part of the expected output is present
    assert "Dummy Power Meter Component" in result.output

def test_gws_layout_mktest():
    """Test that 'gws mktest --no-write does not crash"""
    result = runner.invoke(gws.app, ["layout", "mktest", "--no-write"])
    assert result.exit_code == 0
    # simple test that a tiny part of the expected output is present
