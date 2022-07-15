import contextlib
import os
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from config import ScadaSettings


class NoScadaVars:

    def __init__(self, prefix: str = ScadaSettings.Config.env_prefix):
        self.prefix = prefix

    @contextlib.contextmanager
    def context(self) -> Generator[MonkeyPatch, None, None]:
        """"""
        mpatch = MonkeyPatch()
        with mpatch.context() as m:
            for env_var in os.environ:
                if env_var.startswith(self.prefix):
                    m.delenv(env_var)
            yield m

@pytest.fixture
def no_scada_vars(prefix: str = ScadaSettings.Config.env_prefix) -> Generator[NoScadaVars, None, None]:
    yield NoScadaVars(prefix=prefix)
