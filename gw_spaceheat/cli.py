from pathlib import Path
from typing import Annotated
from typing import Optional

import dotenv
import rich
import typer
from trogon import Trogon
from typer.main import get_group

from admin.cli import app as admin_cli
from actors.config import ScadaSettings
from layout_gen.genlayout import app as layout_cli

__version__: str = "0.2.0"

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help=f"GridWorks Scada CLI, version {__version__}",
)

app.add_typer(admin_cli, name="admin", help="Admin commands.")
app.add_typer(layout_cli, name="layout", help="Layout commands")

@app.command()
def config(env_file: str = ".env"):
    """Show ScadaSettings."""

    dotenv_file = dotenv.find_dotenv(env_file)
    dotenv_file_exists = Path(dotenv_file).exists() if dotenv_file else False
    rich.print("[cyan bold]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    rich.print(f"Env file: <{dotenv_file}>  exists:{dotenv_file_exists}")
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings = ScadaSettings(_env_file=dotenv_file)
    rich.print(settings)
    rich.print("[cyan bold]-----------------------------------------------------------------------------------------------------------\n")

@app.command()
def commands(ctx: typer.Context) -> None:
    """CLI command builder."""
    Trogon(get_group(app), click_context=ctx).run()

def version_callback(value: bool):
    if value:
        print(f"gws {__version__}")
        raise typer.Exit()

@app.callback()
def main_app_callback(
    _version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit."
        ),
    ] = None,
) -> None:
    """Commands for the main gws application"""


# For sphinx:
typer_click_object = typer.main.get_command(app)

if __name__ == "__main__":
    app()
