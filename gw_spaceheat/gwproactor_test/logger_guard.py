import logging
from typing import Optional
from typing import Sequence

import pytest

from gwproactor.config import DEFAULT_BASE_NAME
from gwproactor.config import LoggerLevels
from gwproactor.config import LoggingSettings


class LoggerGuard:
    level: int
    propagate: bool
    handlers: set[logging.Handler]
    filters: set[logging.Filter]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.level = logger.level
        self.propagate = logger.propagate
        self.handlers = set(logger.handlers)
        self.filters = set(logger.filters)

    def restore(self):
        self.logger.setLevel(self.level)
        self.logger.propagate = self.propagate
        curr_handlers = set(self.logger.handlers)
        for handler in (curr_handlers - self.handlers):
            self.logger.removeHandler(handler)
        for handler in (self.handlers - curr_handlers):
            self.logger.addHandler(handler)
        curr_filters = set(self.logger.filters)
        for filter_ in (curr_filters - self.filters):
            self.logger.removeFilter(filter_)
        for filter_ in (self.filters - curr_filters):
            self.logger.addFilter(filter_)
        assert set(self.logger.handlers) == self.handlers
        assert set(self.logger.filters) == self.filters

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()
        return True


class LoggerGuards:
    guards: dict[str, LoggerGuard]

    def __init__(self, logger_names: Optional[Sequence[str]] = None):
        if logger_names is None:
            logger_names = self.default_logger_names()
        self.guards = {logger_name: LoggerGuard(logging.getLogger(logger_name)) for logger_name in logger_names}

    def restore(self):
        for guard in self.guards.values():
            guard.restore()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()
        return True

    @classmethod
    def default_logger_names(cls) -> list[str]:
        return ["root", LoggingSettings().base_log_name] + list(LoggerLevels().qualified_logger_names(DEFAULT_BASE_NAME).values())


@pytest.fixture
def restore_loggers() -> LoggerGuards:
    guards = LoggerGuards()
    yield guards
    guards.restore()
