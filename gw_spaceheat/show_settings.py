from pathlib import Path

import dotenv
from rich import print

from actors.config import ScadaSettings
from command_line_utils import parse_args

if __name__ == "__main__":
    args = parse_args()
    dotenv_file = dotenv.find_dotenv(args.env_file)
    print(f"Env file: <{dotenv_file}>  exists:{Path(dotenv_file).exists()}")
    settings = ScadaSettings(_env_file=dotenv_file)
    print(settings)
