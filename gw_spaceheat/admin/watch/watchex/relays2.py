from logging import Logger
from typing import Optional

from pydantic import BaseModel
from rich.style import Style
from rich.text import Text
from rich.color import Color as RichColor
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Vertical
from textual.widgets import DataTable
from textual.widgets._data_table import CellType # noqa
from textual.widgets._data_table import RowDoesNotExist # noqa

from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState
from admin.watch.widgets.relay2 import RelayControlButtons
from admin.watch.widgets.relay2 import RelayWidgetConfig
from admin.watch.widgets.relays import MqttState
from admin.watch.widgets.relays import Relays

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

class Relays2(Relays):
    _relays: dict[str, RelayWidgetInfo]

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
            yield RelayControlButtons(
                id="relays_control_buttons",
                config=RelayWidgetConfig(),
                show_titles=True,
            )
            yield DataTable(id="message_table", classes="undisplayed")

    def on_mount(self) -> None:
        data_table = self.query_one("#relays_table", DataTable)
        for column_name, width in [
            ("Name", 28),
            ("State", 25),
            ("Deenergize", 25),
            ("Energize", 25),
            # ("Deenergize2", 25),
            # ("Energize2", 25),
        ]:
            data_table.add_column(column_name, key=column_name, width=width)
            message_table = self.query_one("#message_table", DataTable)
            message_table.add_columns(
            "Time", "Type", "Payload",
            )

    def on_relays_relay_state_change(self, message: Relays.RelayStateChange) -> None:
        self.logger.debug("++Relays2.on_relays_relay_state_change  %d", len(message.changes))
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
        self.logger.debug("--Relays2.on_relays_relay_state_change  path:0x%08X", path_dbg)

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
        # if table.cursor_row == row_idx:
        #     row_style_class = "datatable--cursor"
        if row_idx % 2 == 0:
            row_style_class = "datatable--even-row"
        else:
            row_style_class = "datatable--odd-row"
        if relay_name in self._relays:
            relay = self._relays[relay_name]
            textual_row_style = table.get_component_styles(row_style_class)
            rich_row_style = textual_row_style.rich_style
            return {
                "Name": relay.config.channel_name,
                "State": relay.get_state_str(),
                "Deenergize": Text(
                    relay.config.get_state_str(False, show_icon=False),
                    style=Style(
                        color=self.make_translucent(
                            self.app.theme_variables["text-success"],
                            opacity=textual_row_style.opacity,
                            background=textual_row_style.background
                        ),
                        bgcolor=rich_row_style.bgcolor,
                    ),
                    # justify="center",
                ),
                "Energize": Text(
                    relay.config.get_state_str(True, show_icon=False),
                    style=Style(
                            color=self.make_translucent(
                                self.app.theme_variables["text-error"],
                                opacity=textual_row_style.opacity,
                                background=textual_row_style.background,
                            ),
                            bgcolor=rich_row_style.bgcolor,
                        ),
                    # justify="center",
                ),
                # "Deenergize2": Text(
                #     relay.config.get_state_str(False, show_icon=False),
                #     style=Style(
                #         color=self.app.theme_variables["text-success"],
                #         bgcolor=self.app.theme_variables["success"],
                #         bold=True,
                #     ),
                #     justify="center",
                # ),
                # "Energize2": Text(
                #     relay.config.get_state_str(True, show_icon=False),
                #     style=Style(
                #         color=self.app.theme_variables["text-error"],
                #         bgcolor=self.app.theme_variables["error"],
                #         bold=True,
                #     ),
                #     justify="center",
                # ),
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
        buttons = self.query_one("#relays_control_buttons", RelayControlButtons)
        buttons.config = relay_info.config
        buttons.energized = relay_info.get_state()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self._update_buttons(message.row_key.value)