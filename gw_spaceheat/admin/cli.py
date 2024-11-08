from enum import StrEnum

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
    relay_name: str,
    closed: RelayState,
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    settings = AdminClientSettings(target_gnode=target)
    if not json:
        rich.print(settings)
    admin = MQTTAdmin(
        settings=settings,
        relay_name=relay_name,
        closed=closed == RelayState.closed,
        user=user,
        json=json,
    )
    admin.run()


@app.command()
def set_relay(
    target: str,
    relay_name: str,
    closed: RelayState,
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    _set_relay(
        target=target,
        relay_name=relay_name,
        closed=closed,
        user=user,
        json=json,
    )


@app.command()
def run(
    target: str = "dummy_scada1",
    relay_name: str = "relay0",
    closed: RelayState = RelayState.closed,
    user: str = "HeatpumpWizard",
    json: bool = False,
) -> None:
    _set_relay(
        target=target,
        relay_name=relay_name,
        closed=closed,
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
