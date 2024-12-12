import logging
from logging import Logger
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import HorizontalGroup
from textual.logging import TextualHandler
from textual.reactive import Reactive
from textual.reactive import reactive
from textual.widgets import Static
from textual.widgets import Switch

from admin.watch.clients.relay_client import RelayConfig
from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class Relay1(Horizontal):
    config: Reactive[RelayConfig] = reactive(RelayConfig)
    observed: Reactive[Optional[RelayState]] = reactive(None)
    logger: Logger

    def __init__(
        self,
        logger: Logger = module_logger,
        **kwargs,
    ) -> None:
        self.logger = logger
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with HorizontalGroup():
            yield Static(self.config.channel_name, id="relay_channel_name")
            yield Static(self._energized_str(), id="relay_energized")
            yield Static(self.config.deenergized_description, id="relay_switch_label")
            yield Switch(
                animate=False,
                id="relay_switch",
                value=False,
                tooltip=f"{self.config.deenergized_description} / {self.config.energized_description}"
            )

    def watch_config(self):
        if self.query("#relay_channel_name"):
            self.query_one("#relay_channel_name", Static).update(self.config.channel_name)

    def watch_observed(self) -> None:
        if self.query("#relay_channel_name"):
            self.query_one("#relay_energized", Static).update(self._energized_str())
            self.query_one("#relay_switch_label", Static).update(self.config.deenergized_description)

    def _energized_str(self) -> str:
        if self.observed is None:
            return "? / ?"
        elif self.observed.value == RelayEnergized.energized:
            return f"⚡ / {self.config.energized_description}"
        else:
            return f"- / {self.config.deenergized_description}"

    def _energized_name(self) -> str:
        if self.observed is None:
            return "?"
        elif self.observed.value == RelayEnergized.energized:
            return self.config.energized_description
        else:
            return self.config.deenergized_description

    class RelaySwitchChanged(Switch.Changed):

        def __init__(self, relay_widget_id: str, switch: Switch, value: bool) -> None:
            super().__init__(switch, value)
            self.relay_widget_id = relay_widget_id

    def on_switch_changed(self, message: Switch.Changed) -> None:
        self.post_message(Relay1.RelaySwitchChanged(self.id, message.switch, message.value))
