from pathlib import Path

import dotenv
from rich import print

from command_line_utils import parse_args

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

if __name__ == "__main__":
    args = parse_args()
    dotenv_file = dotenv.find_dotenv(args.env_file)
    print("[cyan bold]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(f"Env file: <{dotenv_file}>  exists:{Path(dotenv_file).exists()}")
    settings = AtnSettings(_env_file=dotenv_file)
    print(settings)
    print("[cyan bold]-----------------------------------------------------------------------------------------------------------\n")

