import argparse
import logging
import logging.config
import syslog
import traceback
from typing import Optional

from config import ScadaSettings


def format_exceptions(exceptions: list[BaseException]) -> str:
    s = ""
    # noinspection PyBroadException
    try:
        if exceptions:
            for i, exception in enumerate(exceptions):
                s += f"++ Exception {i + 1:2d} / {len(exceptions)} ++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
                try:
                    s += "".join(traceback.format_exception(exception))
                    s += "\n"
                except BaseException as e:
                    # noinspection PyBroadException
                    try:
                        s += f"ERROR formatting traceback for {e}\n"
                    except:
                        s += "UNEXPECTED ERROR formatting exception.\n"
                s += f"-- Exception {i + 1:2d} / {len(exceptions)} ----------------------------------------------------\n\n"
    except:
        s += "UNEXPECTED ERROR formatting exception.\n"
    return s


def setup_logging(
        args: argparse.Namespace,
        settings: ScadaSettings,
        errors: Optional[list[BaseException]] = None,
        add_screen_handler: bool = True,
) -> None:
    """Get python logging config based on parsed command line args, defaults, environment variables and logging config file.

    The order of precedence is:

        1. Command line arguments
        2. Environment
        3. Defaults

    """
    if errors is None:
        errors: list[BaseException] = []
    else:
        errors.clear()
    config_finished = False
    try:
        # Take any arguments from command line
        try:
            if getattr(args, "verbose", None):
                settings.logging.base_log_level = logging.INFO
                settings.logging.levels.message_summary = logging.DEBUG
            if getattr(args, "message_summary", None):
                settings.logging.levels.message_summary = logging.INFO
        except BaseException as e:
            errors.append(e)

        # Create formatter from settings
        try:
            formatter = settings.logging.formatter.create()
        except BaseException as e:
            formatter = None
            errors.append(e)

        # Set application logger levels
        for logger_name, logger_settings in settings.logging.logger_levels().items():
            try:
                logger = logging.getLogger(logger_name)
                logger.setLevel(logger_settings["level"])
            except BaseException as e:
                errors.append(e)

        # Create handlers from settings, add them to root logger
        if add_screen_handler:
            try:
                screen_handler = logging.StreamHandler()
                if formatter is not None:
                    screen_handler.setFormatter(formatter)
                logging.getLogger().addHandler(screen_handler)
            except BaseException as e:
                errors.append(e)
        try:
            file_handler = settings.logging.file_handler.create(settings.paths.log_dir, formatter)
            if formatter is not None:
                file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
        except BaseException as e:
            errors.append(e)
        config_finished = True
    except BaseException as e:
        config_finished = False
        errors.append(e)
    finally:
        # Try to tell user if something went wrong
        if errors:
            # noinspection PyBroadException
            try:
                s = "ERROR in setup_logging():\n" + format_exceptions(errors)
                if config_finished:
                    logging.error(s)
                else:
                    syslog.syslog(s)
                    print(s)
            except:
                pass
