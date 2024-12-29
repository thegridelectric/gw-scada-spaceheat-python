import logging
from logging import Logger
from typing import Optional

from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.containers import Vertical
from textual.logging import TextualHandler
from textual.reactive import reactive
from textual.reactive import Reactive
from textual.widgets import DataTable
from textual.widgets._data_table import CellType # noqa
from textual.widgets._data_table import RowDoesNotExist # noqa

from admin.watch.watchex.relay_toggle_button import RelayToggleButton
from admin.watch.watchex.relay_widget_info import RelayWidgetInfo
from admin.watch.widgets.relay2 import RelayWidgetConfig
from admin.watch.widgets.relays import MqttState
from admin.watch.widgets.relays import Relays

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class Relays2(Relays):
    BINDINGS = [
        ("n", "toggle_relay", "Toggle selected relay"),
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
            with HorizontalGroup(
                id="relay_toggle_button_container",
            ):
                yield RelayToggleButton(
                    label="bar",
                    id="relay_toggle_button",
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

    def action_toggle_relay(self) -> None:
        self.query_one(
            "#relay_toggle_button",
            RelayToggleButton
        ).action_toggle_relay()

    def on_relays_relay_state_change(self, message: Relays.RelayStateChange) -> None:
        for relay_name, change in message.changes.items():
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

    def _get_relay_row_data(self, relay_name: str) -> dict[str, CellType]:
        if relay_name in self._relays:
            relay = self._relays[relay_name]
            return {
                "Relay Name": relay.config.channel_name,
                "Deenergized Name": relay.config.get_state_str(
                    False,
                    show_icon=False
                ),
                "Energized Name": relay.config.get_state_str(
                    True,
                    show_icon=False
                ),
                "State": relay.get_state_str(),
            }
        return {}

    def _get_relay_row(self, relay_name: str) -> list[str | CellType]:
        return list(self._get_relay_row_data(relay_name).values())

    def _update_relay_row(self, relay_name: str) -> None:
        table = self.query_one("#relays_table", DataTable)
        data = self._get_relay_row_data(relay_name)
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
                        *self._get_relay_row(relay_name),
                        key=relay_name
                    )

    def _update_buttons(self, relay_name: str) -> None:
        relay_info = self._relays[relay_name]
        self.curr_energized = relay_info.get_state()
        self.curr_config = relay_info.config
        self.query_one(
            "#relay_toggle_button_container",
            HorizontalGroup,
        ).border_title = relay_info.config.channel_name
        self.refresh_bindings()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self._update_relay_row(message.row_key.value)
        self._update_buttons(message.row_key.value)
