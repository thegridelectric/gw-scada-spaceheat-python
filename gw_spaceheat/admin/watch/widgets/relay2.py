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
from textual.widgets import Static

from admin.watch.clients.relay_client import RelayConfig

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class RelayWidgetConfig(RelayConfig):
    energized_icon: str = "⚡"
    deenergized_icon: str = "-"
    show_icon: bool = True

    @classmethod
    def from_config(
            cls,
            config: RelayConfig,
            energized_icon: str = "⚡",
            deenergized_icon: str = "-",
            show_icon: bool = True,
    ) -> "RelayWidgetConfig":
        return RelayWidgetConfig(
            energized_icon=energized_icon,
            deenergized_icon=deenergized_icon,
            show_icon=show_icon,
            **config.model_dump()
        )

    def get_state_str(self, energized: Optional[bool], *, show_icon: Optional[bool] = None) -> str:
        if energized is None:
            icon = "?"
            description = "?"
        elif energized:
            icon = self.energized_icon
            description = self.energized_description
        else:
            icon = self.deenergized_icon
            description = self.deenergized_description
        if (show_icon is None and self.show_icon) or show_icon is True:
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

class RelayControlButtons(HorizontalGroup, can_focus=True):
    BINDINGS = [
        ("n", "toggle_relay", "Toggle selected relay")
    ]

    energized: Reactive[Optional[bool]] = reactive(None)
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)
    _show_titles: bool = False
    _maintain_focus: bool = True
    _enable_bindings: bool = False

    def __init__(
        self,
        energized: Optional[bool] = None,
        config: Optional[RelayWidgetConfig] = None,
        logger: logging.Logger = module_logger,
        show_titles: bool = False,
        maintain_focus: bool = True,
        enable_bindings: bool = False,
        **kwargs
    ):
        self.logger = logger
        self._show_titles = show_titles
        self._maintain_focus = maintain_focus
        self._enable_bindings = enable_bindings
        super().__init__(**kwargs)
        self.set_reactive(RelayControlButtons.energized, energized)
        self.set_reactive(RelayControlButtons.config, config or RelayWidgetConfig())

    def compose(self) -> ComposeResult:
        deenergize = Button(
            label=self.config.get_state_str(False),
            disabled=self.energized is not True,
            variant="success",
            id="deenergized_button",
        )
        energize = Button(
            label=self.config.get_state_str(True),
            disabled=self.energized is not False,
            variant="error",
            id="energized_button",
        )
        if self._show_titles:
            deenergize.border_title = "Dee[underline]n[/]ergize"
            energize.border_title = "E[underline]n[/]ergize"
        yield deenergize
        yield energize

    def action_toggle_relay(self) -> None:
        if self.energized is None:
            return
        self.post_message(
            RelayControlButtons.Pressed(
                self.config.about_node_name,
                not self.energized,
            )
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> Optional[bool]:
        if not self._enable_bindings:
            return False
        if action == "toggle_relay" and self.energized is not None:
            return True
        return None

    def watch_energized(self) -> None:
        deenergize = self.query_one("#deenergized_button")
        energize = self.query_one("#energized_button")
        deenergize.disabled = self.energized is not True
        energize.disabled = self.energized is not False
        if self._maintain_focus and (
                self.has_focus or
                energize.has_focus or
                deenergize.has_focus
        ):
            if self.energized is True:
                deenergize.focus()
            elif self.energized is False:
                energize.focus()

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
