import sys
from typing import Optional, Sequence

import dotenv

import load_house
from actors.atn import Atn
from command_line_utils import parse_args, setup_logging
from config import ScadaSettings


def get_atn(argv: Optional[Sequence[str]] = None, start: bool = True) -> Atn:
    if argv is None:
        argv = sys.argv[1:]
        if "-l" not in argv and "--log" not in argv:
            argv.append("-l")
    args = parse_args(argv)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file), log_message_summary=True)
    settings.paths.mkdirs()
    setup_logging(args, settings)
    layout = load_house.load_all(settings.paths.hardware_layout)
    atn = Atn(layout.node("a"), settings, layout)
    if start:
        atn.start()
    return atn

if __name__ == "__main__":
    get_atn()
