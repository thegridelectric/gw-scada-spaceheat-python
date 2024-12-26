import logging

import dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.logging import TextualHandler
from textual.widgets import Header, Footer

from admin.settings import AdminClientSettings
from admin.watch.clients.admin_client import AdminClient
from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayWatchClient
from admin.watch.watchex.relays2 import Relays2
from admin.watch.watchex.relays2 import RelayToggleButton
from admin.watch.widgets.relay2 import RelayControlButtons

logger = logging.getLogger(__name__)
logger.addHandler(TextualHandler())


class WatchExApp(App):
    TITLE: str = "Scada Relay Monitor"
    _admin_client: AdminClient
    _relay_client: RelayWatchClient
    _theme_names: list[str]

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("[", "previous_theme", " <- Theme ->"),
        Binding("]", "next_theme", " "),
        Binding("m", "toggle_messages", "Toggle message display"),
        Binding("c", "toggle_relay_state_colors", "Option: state colors"),
        Binding("b", "toggle_buttons", "Option: double/single buttons"),
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    CSS_PATH = "watchex_app.tcss"


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
        self.set_reactive(WatchExApp.sub_title, self.settings.target_gnode)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        relays = Relays2(logger=logger, id="relays2")
        self._relay_client.set_callbacks(relays.relay_client_callbacks())
        yield relays
        yield Footer()

    def on_mount(self) -> None:
        self._admin_client.start()

    def on_relay_control_buttons_pressed(self, message: RelayControlButtons.Pressed):
        self._relay_client.set_relay(
            message.about_node_name,
            RelayEnergized.energized if message.energize else RelayEnergized.deenergized
        )

    def on_relay_toggle_button_pressed(self, message: RelayToggleButton.Pressed):
        self._relay_client.set_relay(
            message.about_node_name,
            RelayEnergized.energized if message.energize else RelayEnergized.deenergized
        )

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if "light" in self.theme else "textual-light"
        )
        self.clear_notifications()
        self.notify(f"Theme is {self.current_theme.name}")

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

    def action_toggle_messages(self) -> None:
        self.query("#message_table").toggle_class("undisplayed")

    def action_toggle_relay_state_colors(self) -> None:
        relays = self.query_one("#relays2", Relays2)
        relays.state_colors = not relays.state_colors

    def action_toggle_buttons(self) -> None:
        self.query("#relay_control_buttons").toggle_class("undisplayed")
        self.query("#relay_toggle_button_container").toggle_class("undisplayed")
        self.refresh_bindings()

if __name__ == "__main__":
    # https://github.com/koxudaxi/pydantic-pycharm-plugin/issues/1013
    # noinspection PyArgumentList
    settings_ = AdminClientSettings(_env_file=dotenv.find_dotenv())
    settings_.verbosity = logging.DEBUG
    # settings_.paho_verbosity = logging.DEBUG
    app = WatchExApp(settings=settings_)
    app.run()
