import logging
from logging import Logger
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import HorizontalGroup
from textual.logging import TextualHandler
from textual.reactive import Reactive
from textual.reactive import reactive

from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState
from admin.watch.widgets.relay1 import Relay1
from admin.watch.widgets.relay2 import Relay2
from admin.watch.widgets.relay2 import RelayWidgetConfig

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())


class Relay(Horizontal):
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)
    observed: Reactive[Optional[RelayState]] = reactive(None)
    logger: Logger
    energized: Reactive[Optional[bool]] = reactive(None)

    def __init__(
        self,
        config: RelayWidgetConfig,
        observed: Optional[RelayState] = None,
        logger: Logger = module_logger,
        **kwargs,
    ) -> None:
        self.logger = logger
        super().__init__(**kwargs)
        self.config = config
        self.observed = observed

    def compose(self) -> ComposeResult:
        with HorizontalGroup():
            yield Relay1(id = f"{self.id}-v1", logger=self.logger).data_bind(
                config=self.config,
                observed=self.observed,
            )
            yield Relay2(id = f"{self.id}-v2", logger=self.logger).data_bind(
                energized=Relay.energized,
                config=Relay.config,
            )

    def watch_observed(self) -> None:
        if self.observed is None:
            self.energized = None
        else:
            self.energized = True if self.observed.value == RelayEnergized.energized else False
