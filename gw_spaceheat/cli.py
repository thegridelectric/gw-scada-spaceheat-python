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

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Scada CLI",
)

app.add_typer(admin_cli, name="admin", help="Admin commands.")

@app.command()
def config(env_file: str = ".env"):
    """Show ScadaSettings."""

    dotenv_file = dotenv.find_dotenv(env_file)
    dotenv_file_exists = Path(dotenv_file).exists() if dotenv_file else False
    rich.print("[cyan bold]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    rich.print(f"Env file: <{dotenv_file}>  exists:{dotenv_file_exists}")
    settings = ScadaSettings(_env_file=dotenv_file)
    rich.print(settings)
    rich.print("[cyan bold]-----------------------------------------------------------------------------------------------------------\n")

@app.command()
def layout(
    env_file: str = ".env",
    layout_file: Annotated[
        str, typer.Option(
            "--layout-file", "-l",
            help=(
                "Name of layout file (e.g. hardware-layout.json or apple for apple.json). "
                "If path is relative it will be relative to settings.paths.config_dir. "
                "If path has no extension, .json will be assumed. "
                "If not specified default settings.paths.hardware_layout will be used."
            ),
        )
    ] = "",
    raise_errors: Annotated[
        bool, typer.Option(
            "--raise-errors",
            "-r",
            help="Raise any errors immediately to see full call stack."
        )
    ] = False,
    verbose: Annotated[
        bool, typer.Option(
            "--verbose",
            "-v",
            help="Print additional information"
        )
    ] = False,
    table_only: Annotated[
        bool, typer.Option(
            "--table-only",
            "-t",
            help="Print only the table"
        )
    ] = False,
):
    """Show hardware layout."""
    args = ["-e", env_file]
    if layout_file:
        args.extend(["-l", layout_file])
    if raise_errors:
        args.append("-r")
    if verbose:
        args.append("-v")
    if table_only:
        args.append("-t")
    show_layout.main(args)

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
