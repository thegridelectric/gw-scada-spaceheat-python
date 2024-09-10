"""gwcert command-line interface."""

import typer
from trogon import Trogon
from typer.main import get_group
from pathlib import Path

import show_layout
from layout_gen.tst import make_tst_layout

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks hardware layout tools.",
)

@app.command()
def test(
    tag: str = "test",
    write: bool = True,
    src: Path = Path("tests/config/hardware-layout.json")
) -> None:
    working_output_dir = Path(__file__).parent.joinpath("output").resolve()
    working_output_dir.mkdir(exist_ok=True)
    src_control_output_path = Path("tests/config/hardware-layout.json").resolve()
    src_path = src.resolve()
    db = make_tst_layout(src_path)
    if write:
        db.write(src_control_output_path)
    working_path = working_output_dir.joinpath(f"{tag}.generated.json")
    db.write(working_path)
    show_layout.main(["-l", str(working_path)])
    print(".")

@app.command()
def tui(ctx: typer.Context) -> None:
    """Visual CLI command builder."""
    Trogon(get_group(app), click_context=ctx).run()


@app.callback()
def _main() -> None: ...


# For sphinx:
typer_click_object = typer.main.get_command(app)

if __name__ == "__main__":
    app()
