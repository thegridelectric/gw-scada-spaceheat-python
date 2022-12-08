import logging
import os
import time
import sys
from typing import Optional
from typing import Sequence
from pathlib import Path

import dotenv
import rich
from command_line_utils import parse_args
from config import LoggingSettings
from config import Paths
from data_classes.hardware_layout import HardwareLayout
from logging_setup import setup_logging
from tests.atn import AtnSettings

try:
    from tests.atn import Atn2
except ImportError as e:
    raise ImportError(
        f"ERROR. ({e})\n\n"
        "Running the test atn requires an *extra* entry on the pythonpath, the base directory of the repo.\n"
        "Set this with:\n\n"
        "export PYTHONPATH=`pwd`/gw_spaceheat:`pwd`"
    )

def get_atn(argv: Optional[Sequence[str]] = None, start: bool = True) -> "Atn2":
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    env_path = Path(dotenv.find_dotenv(args.env_file))
    dotenv.load_dotenv(env_path)
    settings = AtnSettings(
        paths=Paths(
            name="atn",
            hardware_layout=os.getenv("ATN_PATHS__HARDWARE_LAYOUT", Paths().hardware_layout)
        ),
        logging=LoggingSettings(base_log_name="gridworks.atn")
    )
    settings.paths.mkdirs()
    setup_logging(args, settings)  # type: ignore
    logger = logging.getLogger(settings.logging.base_log_name)
    logger.log(logging.ERROR + 1, f"Env file: [{env_path}]")
    rich.print(settings)
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    a = Atn2("a", settings, layout)
    if start:
        a.start()
    return a


def main(argv: Optional[Sequence[str]] = None):
    if argv is None:
        argv = sys.argv[1:]
    a = get_atn(argv)
    try:
        time.sleep(1)
        a.snap()
        time.sleep(1)
        while True:
            text = input("> ? ")
            if text == "exit()":
                break
            elif text:
                # noinspection PyProtectedMember
                a._logger.info(f"eval(\"{text}\")")
                # noinspection PyBroadException
                try:
                    eval(text)
                except:
                    # noinspection PyProtectedMember
                    a._logger.exception(f"Error with [eval(\"{text}\")]")
    finally:
        a.stop_and_join_thread()


if __name__ == "__main__":
    main()