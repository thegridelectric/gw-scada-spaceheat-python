"""Settings for the GridWorks Scada, readable from environment and/or from env files."""
from gwproactor.config.logging import DEFAULT_BYTES_PER_LOG_FILE
from gwproactor.config.logging import DEFAULT_FRACTIONAL_SECOND_FORMAT
from gwproactor.config.logging import DEFAULT_LOG_FILE_NAME
from gwproactor.config.logging import DEFAULT_LOGGING_FORMAT
from gwproactor.config.logging import DEFAULT_NUM_LOG_FILES
from gwproactor.config.logging import FormatterSettings
from gwproactor.config.logging import LoggerLevels
from gwproactor.config.logging import LoggingSettings
from gwproactor.config.logging import RotatingFileHandlerSettings
from gwproactor.config.mqtt import MQTTClient
from gwproactor.config.paths import DEFAULT_BASE_DIR
from gwproactor.config.paths import DEFAULT_BASE_NAME
from gwproactor.config.paths import DEFAULT_LAYOUT_FILE
from gwproactor.config.paths import DEFAULT_NAME
from gwproactor.config.paths import DEFAULT_NAME_DIR
from gwproactor.config.paths import Paths
from gwproactor.config.proactor_settings import ProactorSettings

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

    # proactor
    "ProactorSettings",
]
