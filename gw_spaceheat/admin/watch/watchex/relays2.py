import logging
from logging import Logger
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from rich.style import Style
from rich.text import Text
from rich.color import Color as RichColor
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Horizontal
from textual.containers import HorizontalGroup
from textual.containers import Vertical
from textual.logging import TextualHandler
from textual.message import Message
from textual.reactive import reactive
from textual.reactive import Reactive
from textual.signal import Signal
from textual.theme import Theme
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets._data_table import CellType # noqa
from textual.widgets._data_table import RowDoesNotExist # noqa

from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState
from admin.watch.widgets.relay2 import RelayControlButtons
from admin.watch.widgets.relay2 import RelayWidgetConfig
from admin.watch.widgets.relays import MqttState
from admin.watch.widgets.relays import Relays

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class RelayWidgetInfo(BaseModel):
    config: RelayWidgetConfig = RelayWidgetConfig()
    observed: Optional[RelayState] = None

    @classmethod
    def get_observed_state(cls, observed) -> Optional[bool]:
        if observed is not None:
            return observed.value == RelayEnergized.energized
        return None

    def get_state(self) -> Optional[bool]:
        return self.get_observed_state(self.observed)

    def get_state_str(self) -> str:
        return self.config.get_state_str(self.get_state())

    def get_energize_str(self) -> str:
        return self.config.get_energize_str(True)

    def get_deenergize_str(self) -> str:
        return self.config.get_energize_str(False)

class RelayToggleButton(Button, can_focus=True):
    BINDINGS = [
        ("n", "toggle_relay", "Toggle selected relay"),
    ]

    energized: Reactive[Optional[bool]] = reactive(None)
    config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)

    def __init__(
        self,
        energized: Optional[bool] = None,
        config: Optional[RelayWidgetConfig] = None,
        logger: logging.Logger = module_logger,
        **kwargs
    ) -> None:
        self.logger = logger
        super().__init__(
            variant=self.variant_from_state(energized),
            **kwargs
        )
        self.set_reactive(RelayToggleButton.energized, energized)
        self.set_reactive(RelayToggleButton.config, config or RelayWidgetConfig())
        self.update_title()

    def update_title(self):
        if self.energized is True:
            self.border_title = f"Dee[underline]n[/]ergize {self.config.channel_name}"
        elif self.energized is False:
            self.border_title = f"E[underline]n[/]ergize {self.config.channel_name}"

    @classmethod
    def variant_from_state(cls, energized: Optional[bool]) -> Literal["default", "success", "error"]:
        if energized is None:
            return "default"
        elif energized:
            return "success"
        return "error"

    def action_toggle_relay(self) -> None:
        if self.energized is not None:
            self.post_message(
                RelayToggleButton.Pressed(
                    self.config.about_node_name,
                    not self.energized,
                )
            )

    def watch_energized(self) -> None:
        self.label = self.config.get_state_str(not self.energized)
        self.disabled = self.energized is None
        self.variant = self.variant_from_state(self.energized)
        self.update_title()

    def watch_config(self):
        self.label = self.config.get_state_str(not self.energized)
        self.update_title()

    class Pressed(Message):
        def __init__(self, about_node_name: str, energize: bool) -> None:
            super().__init__()
            self.about_node_name = about_node_name
            self.energize = energize

    def on_button_pressed(self):
        if self.energized is not None:
            self.post_message(
                RelayToggleButton.Pressed(
                    self.config.about_node_name,
                    not self.energized,
                )
            )


class Relays2(Relays):
    BINDINGS = [
        ("n", "toggle_relay", "Toggle selected relay"),
        ("E", "energize", "Energize relay"),
        ("D", "deenergize", "Deenergize relay"),
    ]
    state_colors: Reactive[bool] = reactive(False)
    curr_energized: Reactive[Optional[bool]] = reactive(None)
    curr_config: Reactive[RelayWidgetConfig] = reactive(RelayWidgetConfig)

    _relays: dict[str, RelayWidgetInfo]
    _highlighted_relay_name: Optional[str] = None

    def __init__(self, logger: Optional[Logger] = None, **kwargs) -> None:
        self._relays = {}
        super().__init__(logger, **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield MqttState(id="mqtt_state")
            yield DataTable(
                id="relays_table",
                zebra_stripes=True,
                cursor_type="row",
            )
            with Horizontal():
                with HorizontalGroup(
                    id="relay_toggle_button_container",
                    classes="undisplayed",
                ):
                    yield RelayToggleButton(
                        label="bar",
                        id="relay_toggle_button",
                    ).data_bind(
                        energized=Relays2.curr_energized,
                        config=Relays2.curr_config,
                    )
                yield RelayControlButtons(
                    id="relay_control_buttons",
                    show_titles=True,
                    enable_bindings=True,
                ).data_bind(
                    energized=Relays2.curr_energized,
                    config=Relays2.curr_config,
                )
            yield DataTable(id="message_table", classes="undisplayed")

    def on_mount(self) -> None:
        data_table = self.query_one("#relays_table", DataTable)
        for column_name, width in [
            ("Relay Name", 28),
            ("Deenergized Name", 25),
            ("Energized Name", 25),
            ("State", 25),
        ]:
            data_table.add_column(column_name, key=column_name, width=width)
        message_table = self.query_one("#message_table", DataTable)
        message_table.add_columns(
        "Time", "Type", "Payload",
        )
        self.app.theme_changed_signal.subscribe(
            self,
            self.handle_theme_change_signal
        )

    def _change_energize(self, energize: bool) -> None:
        if not (
            relay_buttons := self.query_one(
                "#relay_control_buttons",
                RelayControlButtons
            )
        ).has_class("undisplayed"):
            if energize:
                relay_buttons.action_energize()
            else:
                relay_buttons.action_deenergize()
            self.refresh_bindings()
        elif not (
            relay_toggle_button := self.query_one(
                "#relay_toggle_button",
                RelayToggleButton
            )
        ).has_class("undisplayed"):
            relay_toggle_button.action_toggle_relay()

    def action_energize(self) -> None:
        self._change_energize(True)

    def action_deenergize(self) -> None:
        self._change_energize(False)

    def action_toggle_relay(self) -> None:
        self._change_energize(not self.curr_energized)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> Optional[bool]:
        if action == "toggle_relay":
            return not self.query_one(
                "#relay_toggle_button_container",
                HorizontalGroup
            ).has_class("undisplayed")
        else:
            buttons = self.query_one("#relay_control_buttons", RelayControlButtons)
            if buttons.has_class("undisplayed"):
                return False
            else:
                return buttons.check_action(action, parameters)

    def on_relays_relay_state_change(self, message: Relays.RelayStateChange) -> None:
        # self.logger.debug("++Relays2.on_relays_relay_state_change  %d", len(message.changes))
        path_dbg = 0
        for relay_name, change in message.changes.items():
            path_dbg |= 0x00000001
            relay_info = self._relays.get(relay_name, None)
            if relay_info is not None:
                new_state = RelayWidgetInfo.get_observed_state(change.new_state)
                if new_state != relay_info.get_state():
                    relay_info.observed = change.new_state
                    self._update_relay_row(relay_name)
                table = self.query_one("#relays_table", DataTable)
                relay_idx = table.get_row_index(relay_name)
                if relay_idx == table.cursor_row:
                    self._update_buttons(relay_name)
        # self.logger.debug("--Relays2.on_relays_relay_state_change  path:0x%08X", path_dbg)

    @classmethod
    def make_translucent(
        cls,
        color: RichColor | str,
        opacity: float,
        background: Color
    ) -> RichColor:
        if isinstance(color, str):
            color = RichColor.parse(color)
        background_mix = background.multiply_alpha(opacity)
        return (Color.from_rich_color(color) + background_mix).rich_color

    def _get_relay_row_data(self, relay_name: str, row_idx: int) -> dict[str, CellType]:
        table = self.query_one("#relays_table", DataTable)
        if table.cursor_row == row_idx:
            row_style_class = "datatable--cursor"
        elif row_idx % 2 == 0:
            row_style_class = "datatable--even-row"
        else:
            row_style_class = "datatable--odd-row"
        if relay_name in self._relays:
            relay = self._relays[relay_name]
            relay_state = relay.get_state()
            state_text = relay.get_state_str()
            if relay_state is None or not self.state_colors:
                state_renderable = state_text
            else:
                if relay_state:
                    state_theme_variable_color = self.app.theme_variables["text-error"]
                else:
                    state_theme_variable_color = self.app.theme_variables["text-success"]
                textual_row_style = table.get_component_styles(row_style_class)
                state_style = Style(
                    color=self.make_translucent(
                        state_theme_variable_color,
                        opacity=textual_row_style.opacity,
                        background=textual_row_style.background,
                    ),
                    bgcolor=textual_row_style.rich_style.bgcolor,
                )
                state_renderable = Text(state_text, style=state_style)
            return {
                "Relay Name": relay.config.channel_name,
                "Deenergized Name": relay.config.get_state_str(False, show_icon=False),
                "Energized Name": relay.config.get_state_str(True, show_icon=False),
                "State": state_renderable,
            }
        return {}

    def _get_relay_row(self, relay_name: str, row_idx: int) -> list[str | CellType]:
        return list(self._get_relay_row_data(relay_name, row_idx).values())

    def _update_relay_row(self, relay_name: str) -> None:
        table = self.query_one("#relays_table", DataTable)
        data = self._get_relay_row_data(relay_name, table.get_row_index(relay_name))
        for column_name, value in data.items():
            table.update_cell(relay_name, column_name, value)

    def on_relays_config_change(self, message: Relays.ConfigChange) -> None:
        message.prevent_default()
        table = self.query_one("#relays_table", DataTable)
        for relay_name, change in message.changes.items():
            relay_info = self._relays.get(relay_name, None)
            if relay_info is not None:
                if change.new_config is None:
                    self._relays.pop(relay_name)
                    table.remove_row(relay_name)
                else:
                    new_config = RelayWidgetConfig.from_config(change.new_config)
                    if new_config != relay_info.config:
                        relay_info.config = new_config
                        self._update_relay_row(relay_name)
            else:
                if change.new_config is not None:
                    self._relays[relay_name] = RelayWidgetInfo(
                        config=RelayWidgetConfig.from_config(change.new_config)
                    )
                    table.add_row(
                        *self._get_relay_row(relay_name,table.row_count),
                        key=relay_name
                    )

    def _update_buttons(self, relay_name: str) -> None:
        relay_info = self._relays[relay_name]
        self.curr_energized = relay_info.get_state()
        self.curr_config = relay_info.config
        self.refresh_bindings()

    def _update_table(self):
        for relay_name in self._relays:
            self._update_relay_row(relay_name)

    def handle_theme_change_signal(self, _signal: Signal[Theme]) -> None:
        self._update_table()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        if self._highlighted_relay_name is not None:
            self._update_relay_row(self._highlighted_relay_name)
        self._highlighted_relay_name = message.row_key.value
        self._update_relay_row(self._highlighted_relay_name)
        self._update_buttons(self._highlighted_relay_name)

    def watch_state_colors(self):
        self._update_table()