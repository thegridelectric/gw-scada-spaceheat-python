from enum import StrEnum

import dotenv
import rich
import typer

from gwproactor.command_line_utils import get_settings, print_settings

from admin.client import MQTTAdmin
from admin.settings import AdminClientSettings

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Scada Admin Client",
)


class RelayState(StrEnum):
    open = "0"
    closed = "1"


def _set_relay(
    *,
    target: str,
    open_relay: bool,
    env: str = ".env",
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    # noinspection PyArgumentList
    settings = AdminClientSettings(
        target_gnode=target,
        _env_file=dotenv.find_dotenv(env)
    )
    if not json:
        rich.print(settings)
    admin = MQTTAdmin(
        settings=settings,
        open_relay=open_relay,
        user=user,
        json=json,
    )
    admin.run()


@app.command()
def set_relay(
    target: str,
    open_relay: bool,
    env_file: str = ".env",
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    _set_relay(
        target=target,
        open_relay=open_relay,
        env=env_file,
        user=user,
        json=json,
    )


@app.command()
def run(
    target: str = "d1.isone.me.versant.keene.orange.scada",
    open_relay: bool = True,
    env_file: str = ".env",
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    _set_relay(
        target=target,
        open_relay=open_relay,
        env=env_file,
        user=user,
        json=json,
    )


@app.command()
def config(
    target: str = "",
    env_file: str = ".env",
) -> None:
    settings = get_settings(settings_type=AdminClientSettings, env_file=env_file)
    settings.target_gnode = target
    print_settings(settings=settings, env_file=env_file)


@app.callback()
def _main() -> None: ...


if __name__ == "__main__":
    app()
