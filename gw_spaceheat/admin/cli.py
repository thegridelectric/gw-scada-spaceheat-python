import logging
from enum import StrEnum
from typing import Annotated

import dotenv
import rich
import typer

from gwproactor.command_line_utils import print_settings

from admin.tdemo.cli import app as tdemo_cli
from admin.settings import AdminClientSettings
from admin.watch.relay_app import RelaysApp
from admin.watch.watchex.watchex_app import WatchExApp

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Scada Admin Client",
)

app.add_typer(tdemo_cli, name="demo", help="Textual demo commands.")

DEFAULT_TARGET: str = "d1.isone.me.versant.keene.orange.scada"

class RelayState(StrEnum):
    open = "0"
    closed = "1"

def watch_settings(
    target: str = "",
    env_file: str = ".env",
    verbose: int = 0,
    paho_verbose: int = 0
) -> AdminClientSettings:
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings = AdminClientSettings(
        _env_file=dotenv.find_dotenv(env_file),
    )
    if target:
        settings.target_gnode = target
    elif not settings.target_gnode:
        settings.target_gnode = DEFAULT_TARGET
    if verbose:
        if verbose == 1:
            verbosity = logging.INFO
        else:
            verbosity = logging.DEBUG
        settings.verbosity = verbosity
    if paho_verbose:
        if paho_verbose == 1:
            paho_verbosity = logging.INFO
        else:
            paho_verbosity = logging.DEBUG
        settings.paho_verbosity = paho_verbosity
    return settings

@app.command()
def watch(
    target: str = "",
    env_file: str = ".env",
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose", "-v", count=True
        )
    ] = 0,
    paho_verbose: Annotated[
        int,
        typer.Option(
            "--paho-verbose", count=True
        )
    ] = 0
) -> None:
    """Watch and set relays."""
    settings = watch_settings(target, env_file, verbose, paho_verbose)
    rich.print(settings)
    watch_app = RelaysApp(settings=settings)
    watch_app.run()

@app.command()
def watchex(
    target: str = "",
    env_file: str = ".env",
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose", "-v", count=True
        )
    ] = 0,
    paho_verbose: Annotated[
        int,
        typer.Option(
            "--paho-verbose", count=True
        )
    ] = 0
) -> None:
    """Watch and set relays with experimental features"""
    settings = watch_settings(target, env_file, verbose, paho_verbose)
    rich.print(settings)
    watch_app = WatchExApp(settings=settings)
    watch_app.run()

@app.command()
def config(
    target: str = "",
    env_file: str = ".env",
        verbose: Annotated[
            int,
            typer.Option(
                "--verbose", "-v", count=True
            )
        ] = 0,
        paho_verbose: Annotated[
            int,
            typer.Option(
                "--paho-verbose", count=True
            )
        ] = 0
) -> None:
    """Show admin settings."""
    settings = watch_settings(target, env_file, verbose, paho_verbose)
    print_settings(settings=settings, env_file=env_file)


@app.callback()
def _main() -> None: ...


if __name__ == "__main__":
    app()
