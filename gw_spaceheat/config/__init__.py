"""Settings for the GridWorks Scada, readable from environment and/or from env files."""
from .logging import DEFAULT_LOGGING_FORMAT
from .logging import DEFAULT_FRACTIONAL_SECOND_FORMAT
from .logging import DEFAULT_LOG_FILE_NAME
from .logging import DEFAULT_BYTES_PER_LOG_FILE
from .logging import DEFAULT_NUM_LOG_FILES
from .logging import FormatterSettings
from .logging import LoggerLevels
from .logging import LoggingSettings
from .logging import RotatingFileHandlerSettings

from .mqtt import MQTTClient
from .paths import DEFAULT_BASE_DIR
from .paths import DEFAULT_BASE_NAME
from .paths import DEFAULT_NAME
from .paths import DEFAULT_NAME_DIR
from .paths import DEFAULT_LAYOUT_FILE
from .paths import Paths
from .scada import ScadaSettings

DEFAULT_ENV_FILE = ".env"

__all__ = [
    # logging
    "DEFAULT_LOGGING_FORMAT",
    "DEFAULT_FRACTIONAL_SECOND_FORMAT",
    "DEFAULT_LOG_FILE_NAME",
    "DEFAULT_BYTES_PER_LOG_FILE",
    "DEFAULT_NUM_LOG_FILES",
    "FormatterSettings",
    "LoggerLevels",
    "LoggingSettings",
    "RotatingFileHandlerSettings",

    # mqtt
    "MQTTClient",

    # paths
    "DEFAULT_ENV_FILE",
    "DEFAULT_BASE_DIR",
    "DEFAULT_BASE_NAME",
    "DEFAULT_NAME",
    "DEFAULT_NAME_DIR",
    "DEFAULT_LAYOUT_FILE",
    "Paths",

    # scada
    "ScadaSettings",

]
