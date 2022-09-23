import sys
from typing import Optional, Sequence

import dotenv

import load_house
from actors.atn import Atn
from command_line_utils import parse_args, setup_logging
from config import ScadaSettings, Paths


def get_atn(argv: Optional[Sequence[str]] = None, start: bool = True, update_root_logger: bool = False) -> Atn:
    if argv is None:
        argv = sys.argv[1:]
        if "-v" not in argv and "--verbose" not in argv:
            argv.append("-v")
    args = parse_args(argv)
    dotenv.load_dotenv(dotenv.find_dotenv(args.env_file))
    settings = ScadaSettings(
        paths=Paths(
            name="atn",
            hardware_layout=Paths().hardware_layout
        ),
    )
    settings.paths.mkdirs()
    setup_logging(args, settings)
    layout = load_house.load_all(settings)
    atn = Atn("a", settings, layout)
    if start:
        atn.start()
    return atn

if __name__ == "__main__":
    get_atn()
