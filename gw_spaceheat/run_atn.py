import logging
import sys
from typing import Optional, Sequence

import dotenv

import load_house
from actors.atn import Atn
from command_line_utils import parse_args, setup_logging
from actors2.config import ScadaSettings, Paths
from proactor.config import LoggingSettings


def get_atn(argv: Optional[Sequence[str]] = None, start: bool = True) -> Atn:
    if argv is None:
        argv = sys.argv[1:]
        if "-v" not in argv and "--verbose" not in argv:
            argv.append("-v")
    args = parse_args(argv)
    env_path = dotenv.find_dotenv(args.env_file)
    dotenv.load_dotenv(env_path)
    settings = ScadaSettings(
        paths=Paths(
            name="atn",
            hardware_layout=Paths().hardware_layout
        ),
        logging=LoggingSettings(base_log_name="gridworks.atn")
    )
    settings.paths.mkdirs()
    setup_logging(args, settings)
    logger = logging.getLogger(settings.logging.base_log_name)
    logger.info(f"Env file: {env_path}")
    import rich
    rich.print(settings)
    layout = load_house.load_all(settings)
    atn = Atn("a", settings, layout)
    if start:
        atn.start()
    return atn

if __name__ == "__main__":
    get_atn()
