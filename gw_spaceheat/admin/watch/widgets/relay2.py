import logging
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.app import RenderResult
from textual.containers import Horizontal
from textual.containers import HorizontalGroup
from textual.logging import TextualHandler
from textual.message import Message
from textual.reactive import Reactive
from textual.reactive import reactive
from textual.widgets import Button
from textual.widgets import Rule
from textual.widgets import Static

from admin.watch.clients.relay_client import RelayConfig

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class RelayWidgetConfig(RelayConfig):
    energized_icon: str = "⚡"
    deenergized_icon: str = "-"
    show_icon: bool = True

    def get_state_str(self, energized: bool) -> str:
        if energized is None:
            icon = "?"
            description = "?"
        elif energized:
            icon = self.energized_icon
            description = self.energized_description
        else:
            icon = self.deenergized_icon
            description = self.deenergized_description
        if self.show_icon:
            return f"{icon} / {description}"
        return description

class RelayStateText(Static):
    energized: Reactive[Optional[bool]] = reactive(None)
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)

    def __init__(
        self,
        energized: Optional[bool] = None,
        config: Optional[RelayWidgetConfig] = None,
        *args,
        logger: logging.Logger = module_logger,
        **kwargs
    ):
        self.logger = logger
        super().__init__(*args, **kwargs)
        self.energized = energized
        self.config = config or RelayWidgetConfig()

    def render(self) -> RenderResult:
        return self.config.get_state_str(self.energized)

class RelayControlButtons(HorizontalGroup):
    energized: Reactive[Optional[bool]] = reactive(None)
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)

    def __init__(
        self,
        energized: Optional[bool] = None,
        config: Optional[RelayWidgetConfig] = None,
        logger: logging.Logger = module_logger,
        **kwargs
    ):
        self.logger = logger
        super().__init__(**kwargs)
        self.set_reactive(RelayControlButtons.energized, energized)
        self.set_reactive(RelayControlButtons.config, config or RelayWidgetConfig())

    def compose(self) -> ComposeResult:
        yield Button(
            label=self.config.get_state_str(False),
            disabled=self.energized is not True,
            variant="success",
            id="deenergized_button",
        )
        yield Button(
            label=self.config.get_state_str(True),
            disabled=self.energized is not False,
            variant="error",
            id="energized_button",
        )

    def watch_energized(self) -> None:
        self.query_one("#deenergized_button").disabled = self.energized is not True
        self.query_one("#energized_button").disabled = self.energized is not False

    def watch_config(self):
        self.query_one("#deenergized_button").label = self.config.get_state_str(False)
        self.query_one("#energized_button").label = self.config.get_state_str(True)

    class Pressed(Message):
        def __init__(self, about_node_name: str, energize: bool) -> None:
            super().__init__()
            self.about_node_name = about_node_name
            self.energize = energize

    @on(Button.Pressed, selector="#deenergized_button")
    def deenergize_pressed(self):
        self.post_message(
            RelayControlButtons.Pressed(
                self.config.about_node_name,
                False,
            )
        )

    @on(Button.Pressed, selector="#energized_button")
    def energize_pressed(self):
        self.post_message(
            RelayControlButtons.Pressed(
                self.config.about_node_name,
                True,
            )
        )

class Relay2(Horizontal):
    energized: Reactive[Optional[bool]] = reactive(None)
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)
    logger: logging.Logger

    def __init__(self, *args, logger:logging.Logger = module_logger, **kwargs) -> None:
        self.logger = logger
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Static(self.config.channel_name, id="relay_channel_name")
        yield RelayStateText(
            energized=self.energized,
            config=self.config,
            id="state_text",
            logger=self.logger,
        ).data_bind(energized=Relay2.energized, config=Relay2.config)
        yield RelayControlButtons(
            energized=self.energized,
            config=self.config,
            id="buttons",
            logger=self.logger,
        ).data_bind(energized=Relay2.energized, config=Relay2.config)

    def watch_config(self):
        if self.query("#relay_channel_name"):
            self.query_one("#relay_channel_name", Static).update(self.config.channel_name)
