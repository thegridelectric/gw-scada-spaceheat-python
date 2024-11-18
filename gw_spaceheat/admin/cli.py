from enum import StrEnum

import dotenv
import rich
import typer

from gwproactor.command_line_utils import get_settings, print_settings

from admin.set_client import SetAdminClient
from admin.settings import AdminClientSettings
from admin.watch_client import WatchAdminClient

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Scada Admin Client",
)

DEFAULT_TARGET: str = "d1.isone.me.versant.keene.orange.scada"

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
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings = AdminClientSettings(
        target_gnode=target,
        _env_file=dotenv.find_dotenv(env)
    )
    if not json:
        rich.print(settings)
    admin = SetAdminClient(
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
def watch(
    target: str = "",
    env_file: str = ".env",
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings = AdminClientSettings(
        _env_file=dotenv.find_dotenv(env_file)
    )
    if target:
        settings.target_gnode = target
    elif not settings.target_gnode:
        settings.target_gnode = DEFAULT_TARGET
    if not json:
        rich.print(settings)
    admin = WatchAdminClient(
        settings=settings,
        user=user,
        json=json,
    )
    admin.run()


@app.command()
def run(
    target: str = DEFAULT_TARGET,
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
