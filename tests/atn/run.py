import logging
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

import dotenv
import rich

from command_line_utils import check_tls_paths_present
from command_line_utils import parse_args
from gwproactor.config import LoggingSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproactor import setup_logging

try:
    from tests.atn import AtnSettings
    from tests.atn import Atn
except ImportError as e:
    raise ImportError(
        f"ERROR. ({e})\n\n"
        "Running the test atn requires an *extra* entry on the pythonpath, the base directory of the repo.\n"
        "Set this with:\n\n"
        "  export PYTHONPATH=$PYTHONPATH:`pwd`\n"
    )


def get_atn(argv: Optional[Sequence[str]] = None, start: bool = True) -> "Atn":
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    env_path = Path(dotenv.find_dotenv(args.env_file))
    dotenv.load_dotenv(env_path)
    settings = AtnSettings(
        logging=LoggingSettings(base_log_name="gridworks.atn"),
    )
    if args.dry_run:
        rich.print(f"Env file: <{env_path}>  exists:{env_path.exists()}")
        rich.print(settings)
        missing_tls_paths_ = check_tls_paths_present(settings, raise_error=False)
        if missing_tls_paths_:
            rich.print(missing_tls_paths_)
        sys.exit(0)
    settings.paths.mkdirs()
    setup_logging(args, settings)  # type: ignore
    logger = logging.getLogger(settings.logging.base_log_name)
    logger.log(logging.ERROR + 1, f"Env file: [{env_path}]")
    rich.print(settings)
    check_tls_paths_present(settings)
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    a = Atn("a", settings, layout)
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
            if text == "exit()" or text == "q":
                break
            elif text:
                # noinspection PyProtectedMember
                a._logger.info(f'eval("{text}")')
                # noinspection PyBroadException
                try:
                    eval(text)
                except:
                    # noinspection PyProtectedMember
                    a._logger.exception(f'Error with [eval("{text}")]')
    finally:
        a.stop_and_join_thread()


if __name__ == "__main__":
    main()
