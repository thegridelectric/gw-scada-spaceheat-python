import argparse
import logging
import logging.handlers
from typing import Optional

from config import Paths, ScadaSettings
from logging_config import LoggingSettings, LoggerLevels, DEFAULT_LOG_FILE_NAME, RotatingFileHandlerSettings
from logging_setup import setup_logging
from test.test_logging_config import get_exp_formatted_time


def test_get_default_logging_config(caplog, capsys):
    paths = Paths()
    paths.mkdirs()
    settings = ScadaSettings(logging=LoggingSettings(base_log_level=logging.INFO))
    root = logging.getLogger()
    old_root_level = root.getEffectiveLevel()
    pytest_root_handlers = len(root.handlers)
    errors = []

    setup_logging(argparse.Namespace(message_summary=True), settings, errors=errors)
    assert len(errors) == 0

    # root logger changes
    assert root.getEffectiveLevel() == old_root_level
    assert len(root.handlers) == pytest_root_handlers + 2
    stream_handler: Optional[logging.StreamHandler] = None
    file_handler: Optional[logging.handlers.RotatingFileHandler] = None
    for i in range(-1, -3, -1):
        handler = root.handlers[i]
        if isinstance(handler, logging.StreamHandler):
            stream_handler = handler
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            file_handler = handler
    assert stream_handler is not None
    assert file_handler is not None
    assert logging.getLogger("gridworks").getEffectiveLevel() == settings.logging.base_log_level
    # Sub-logger levels
    logger_names = settings.logging.qualified_logger_names()

    # Check if loggers have been added or renamed
    assert set(LoggingSettings().levels.__fields__.keys()) == {"message_summary", "lifecycle", "comm_event"}
    for field_name in settings.logging.levels.__fields__:
        logger_level = logging.getLogger(logger_names[field_name]).level
        settings_level = getattr(settings.logging.levels, field_name)
        assert logger_level == settings_level
    assert logging.getLogger(logger_names["base"]).level == settings.logging.base_log_level

    assert len(caplog.records) == 0

    # Check logger filter by level and message formatting.
    formatter = settings.logging.formatter.create()
    text = ""
    for i, logger_name in enumerate([settings.logging.base_log_name] + list(logger_names.values())):
        logger = logging.getLogger(logger_name)
        msg = "%d: %s"
        logger.debug(msg, i, logger.name)
        assert len(caplog.records) == 0
        logger.info(msg, i, logger.name)
        assert len(caplog.records) == 1
        exp_msg = "%s %s\n" % (get_exp_formatted_time(caplog.records[-1], formatter), msg % (i, logger.name))
        assert capsys.readouterr().err == exp_msg
        text += exp_msg
        caplog.clear()

    # Check file contents
    log_path = settings.paths.log_dir / DEFAULT_LOG_FILE_NAME
    with log_path.open() as f:
        log_contents = f.read()
    assert log_contents == text


def test_rollover():
    paths = Paths()
    paths.mkdirs()

    def _log_dir_size() -> int:
        return sum(f.stat().st_size for f in paths.log_dir.glob('**/*') if f.is_file())
    bytes_per_log_file = 50
    num_log_files = 3
    settings = ScadaSettings(
        logging=LoggingSettings(
            file_handler=RotatingFileHandlerSettings(
                bytes_per_log_file=bytes_per_log_file,
                num_log_files=num_log_files,
            )
        )
    )
    errors = []
    setup_logging(argparse.Namespace(verbose=True), settings, errors=errors)
    assert len(errors) == 0
    assert _log_dir_size() == 0
    logger = logging.getLogger("gridworks.general")
    for _ in range(300):
        logger.info("12345678901234567890")
    assert _log_dir_size() <= bytes_per_log_file * num_log_files
    assert len(list(paths.log_dir.glob('**/*'))) == num_log_files
