from pathlib import Path
from typing import Annotated

import dotenv
import rich
import typer
from trogon import Trogon
from typer.main import get_group

import show_layout
from admin.cli import app as admin_cli
from actors.config import ScadaSettings
from layout_gen.genlayout import app as layout_cli

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Scada CLI",
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


@app.callback()
def main_app_callback() -> None: ...


# For sphinx:
typer_click_object = typer.main.get_command(app)

if __name__ == "__main__":
    app()
