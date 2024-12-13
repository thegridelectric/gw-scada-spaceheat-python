import logging
import random

import dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.logging import TextualHandler
from textual.reactive import reactive
from textual.reactive import Reactive
from textual.widgets import Header, Footer

from admin.settings import AdminClientSettings
from admin.watch.clients.admin_client import AdminClient
from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayWatchClient
from admin.watch.widgets.relay1 import Relay1
from admin.watch.widgets.relay2 import RelayControlButtons
from admin.watch.widgets.relays import Relay
from admin.watch.widgets.relays import Relays

logger = logging.getLogger(__name__)
logger.addHandler(TextualHandler())


class RelaysApp(App):
    TITLE: str = "I am a teapot"
    title: str = reactive(TITLE)
    dark: Reactive[bool]
    _admin_client: AdminClient
    _relay_client: RelayWatchClient
    _theme_names: list[str]

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("n", "shuffle_title", "Shuffle title"),
        ("t", "reset_title", "Reset title"),
        ("a", "previous_theme", "Previous theme"),
        ("s", "next_theme", "Next theme"),
        Binding("q", "quit", "Quit", show=True, priority=True),
    ]
    CSS_PATH = "relay_app.tcss"

    def __init__(
        self,
        *,
        settings: AdminClientSettings = AdminClientSettings(),
    ) -> None:
        self.settings = settings
        logger.setLevel(settings.verbosity)
        if self.settings.paho_verbosity is not None:
            paho_logger = logging.getLogger("paho." + __name__)
            paho_logger.addHandler(TextualHandler())
            paho_logger.setLevel(settings.paho_verbosity)
        else:
            paho_logger = None
        self._relay_client = RelayWatchClient(logger=logger)
        self._admin_client = AdminClient(
            settings,
            subclients=[self._relay_client],
            logger=logger,
            paho_logger=paho_logger,
        )
        super().__init__()
        self._theme_names = [
            theme for theme in self.available_themes if theme != "textual-ansi"
        ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        relays = Relays(logger=logger)
        self._relay_client.set_callbacks(relays.relay_client_callbacks())
        yield relays
        yield Footer()

    def on_mount(self) -> None:
        self._admin_client.start()

    def on_relay1_relay_switch_changed(self, message: Relay1.RelaySwitchChanged):
        try:
            relay_widget = self.query_one(
                f"#{message.relay_widget_id}",
                Relay,
            )
            self._relay_client.set_relay(
                relay_widget.config.about_node_name,
                RelayEnergized.energized if message.switch.value else RelayEnergized.deenergized
            )
        except NoMatches:
            ...

    def on_relay_control_buttons_pressed(self, message: RelayControlButtons.Pressed):
        try:
            self._relay_client.set_relay(
                message.about_node_name,
                RelayEnergized.energized if message.energize else RelayEnergized.deenergized
            )
        except NoMatches:
            ...

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_shuffle_title(self) -> None:
        lst = list(self.title)
        random.shuffle(lst)
        self.title = "".join(lst)

    def action_reset_title(self) -> None:
        self.title = self.TITLE

    async def action_quit(self) -> None:
        self._admin_client.stop()
        await super().action_quit()

    def _change_theme(self, distance: int):
        self.theme = self._theme_names[
            (self._theme_names.index(self.current_theme.name) + distance)
            % len(self._theme_names)
        ]
        self.clear_notifications()
        self.notify(f"Theme is {self.current_theme.name}")

    def action_next_theme(self) -> None:
        self._change_theme(1)

    def action_previous_theme(self) -> None:
        self._change_theme(-1)


if __name__ == "__main__":
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings_ = AdminClientSettings(_env_file=dotenv.find_dotenv())
    settings_.verbosity = logging.DEBUG
    # settings_.paho_verbosity = logging.DEBUG
    app = RelaysApp(settings=settings_)
    app.run()
