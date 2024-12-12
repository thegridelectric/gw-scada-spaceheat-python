import datetime
import json
import logging
from logging import Logger
from typing import Optional

from gwproto import MQTTTopic
from gwproto.named_types import SnapshotSpaceheat
from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.logging import TextualHandler
from textual.messages import Message
from textual.reactive import Reactive
from textual.reactive import reactive

from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets import Static
from textual.widgets import Switch

from admin.watch.clients.admin_client import type_name
from admin.watch.clients.constrained_mqtt_client import ConstrainedMQTTClient
from admin.watch.clients.relay_client import ObservedRelayStateChange
from admin.watch.clients.relay_client import RelayClientCallbacks
from admin.watch.clients.relay_client import RelayConfig
from admin.watch.clients.relay_client import RelayConfigChange
from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState
from admin.watch.widgets.constrained_mqtt_widget import Mqtt

from named_types import LayoutLite

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())

class MqttState(Widget):

    mqtt_state: Reactive[str] = reactive(ConstrainedMQTTClient.States.stopped, layout=True)
    message_count: Reactive[int] = reactive(0, layout=True)
    snapshot_count: Reactive[int] = reactive(0, layout=True)
    layout_count: Reactive[int] = reactive(0, layout=True)

    def render(self) -> str:
        return (
            f"MQTT broker connection: {self.mqtt_state:12s}  "
            f"Messages received: {self.message_count}  "
            f"Snapshots: {self.snapshot_count}  "
            f"Layouts: {self.layout_count}"
        )

class Relay(HorizontalGroup):
    config: Reactive[RelayConfig] = reactive(RelayConfig)
    observed: Reactive[Optional[RelayState]] = reactive(None)
    user_set: Reactive[Optional[RelayState]] = reactive(None)
    logger: Logger

    def __init__(
        self,
        config: RelayConfig,
        observed: Optional[RelayState] = None,
        user_set: Optional[RelayState] = None,
        logger: Logger = module_logger,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.observed = observed
        self.user_set = user_set
        self.logger = logger

    def compose(self) -> ComposeResult:
        yield Static(self.config.channel_name, id="relay_channel_name")
        yield Static(self._energized_str(), id="relay_energized")
        yield Static(self.config.deenergized_name, id="relay_switch_label")
        yield Switch(
            animate=False,
            id="relay_switch",
            value=False,
            tooltip=f"{self.config.deenergized_name} / {self.config.energized_name}"
        )

    def update_state_widgets(self) -> None:
        self.query_one("#relay_energized", Static).update(self._energized_str())
        self.query_one("#relay_switch_label", Static).update(self.config.deenergized_name)
        # self.query_one("#relay_switch", Switch).value = (
        #     self.observed is not None
        #     and self.observed.value == RelayEnergized.energized
        # )

    def _energized_str(self) -> str:
        if self.observed is None:
            return "? / ?"
        elif self.observed.value == RelayEnergized.energized:
            return f"⚡ / {self.config.energized_name}"
        else:
            return f"-  / {self.config.deenergized_name}"

    def _energized_name(self) -> str:
        if self.observed is None:
            return "?"
        elif self.observed.value == RelayEnergized.energized:
            return self.config.energized_name
        else:
            return self.config.deenergized_name

    class RelaySwitchChanged(Switch.Changed):

        def __init__(self, relay_widget_id: str, switch: Switch, value: bool) -> None:
            super().__init__(switch, value)
            self.relay_widget_id = relay_widget_id

    def on_switch_changed(self, message: Switch.Changed) -> None:
        energized = RelayEnergized.energized if message.value else RelayEnergized.energized
        now = datetime.datetime.now()
        if self.user_set is None:
            self.user_set = RelayState(
                value=energized,
                time=now,
            )
        else:
            self.user_set.value = energized
            self.user_set.time = now
        self.mutate_reactive(Relay.user_set)
        self.update_state_widgets()
        self.post_message(Relay.RelaySwitchChanged(self.id, message.switch, message.value))

class Relays(Widget):
    mqtt_state: Reactive[str] = reactive(ConstrainedMQTTClient.States.stopped)
    logger: Logger

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or module_logger
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield MqttState(id="mqtt_state")
            yield VerticalScroll(id="relay_scroll")
            yield DataTable(id="message_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(
            "Time", "Type", "Payload",
        )

    class RelayStateChange(Message):

        def __init__(self, changes: dict[str, ObservedRelayStateChange]) -> None:
            self.changes = changes
            super().__init__()

    class ConfigChange(Message):

        def __init__(self, changes: dict[str, RelayConfigChange]) -> None:
            self.changes = changes
            super().__init__()

    class Snapshot(Message):
        def __init__(self, snapshot: SnapshotSpaceheat) -> None:
            self.snapshot = snapshot
            super().__init__()

    class Layout(Message):
        def __init__(self, layout: LayoutLite) -> None:
            self.layout = layout
            super().__init__()

    @classmethod
    def _relay_widget_name(cls, relay_name: str) -> str:
        return f"relay-widget-{relay_name}"

    @classmethod
    def _relay_widget_query_name(cls, relay_name: str) -> str:
        return f"#{cls._relay_widget_name(relay_name)}"

    def on_relays_relay_state_change(self, message: RelayStateChange) -> None:
        # self.logger.debug("++on_relays_relay_state_change  %d", len(message.changes))
        path_dbg = 0
        for relay_name, change in message.changes.items():
            path_dbg |= 0x00000001
            try:
                widget = self.query_one(
                    self._relay_widget_query_name(relay_name), Relay
                )
                widget.observed = change.new_state
                # self.logger.debug(
                #     "Changed <%s> to %s",
                #     self._relay_widget_query_name(relay_name),
                #     widget.observed
                # )
                widget.mutate_reactive(Relay.observed)
                widget.update_state_widgets()
            except NoMatches:
                path_dbg |= 0x00000002
        # self.logger.debug("--on_relays_relay_state_change  path:0x%08X", path_dbg)

    def on_relays_config_change(self, message: ConfigChange) -> None:
        new_configs = []
        for relay_name, change in message.changes.items():
            try:
                widget = self.query_one(
                    self._relay_widget_query_name(relay_name), Relay
                )
                if change.new_config is None:
                    widget.remove()
                else:
                    widget.config = change.new_config
                    widget.mutate_reactive(Relay.config)
                    widget.update_state_widgets()
            except NoMatches:
                if change.new_config is not None:
                    new_configs.append((self._relay_widget_name(relay_name), change.new_config))
        sorted_new_configs = sorted(new_configs, key=lambda x: x[1].channel_name)
        for widget_id, new_config in sorted_new_configs:
            self.query_one("#relay_scroll").mount(
                Relay(config=new_config, id=widget_id, logger=self.logger)
            )

    def on_relays_layout(self, message: Layout) -> None:
        self.query_one(MqttState).message_count += 1
        self.query_one(MqttState).layout_count += 1
        self.query_one(DataTable).add_row(
            datetime.datetime.now(),
            type_name(LayoutLite),
            message.layout,
        )

    def on_relays_snapshot(self, message: Snapshot) -> None:
        self.query_one(MqttState).message_count += 1
        self.query_one(MqttState).snapshot_count += 1
        self.query_one(DataTable).add_row(
            datetime.datetime.now(),
            type_name(SnapshotSpaceheat),
            message.snapshot,
        )
    
    def on_mqtt_state_change(self, message: Mqtt.StateChange):
        self.query_one(MqttState).mqtt_state = message.new_state

    def on_mqtt_receipt(self, message: Mqtt.Receipt):
        self.query_one(MqttState).message_count += 1
        payload = json.loads(message.payload.decode("utf-8"))
        self.query_one(DataTable).add_row(
            datetime.datetime.now(),
            MQTTTopic.decode(message.topic).message_type,
            str(payload.get("Payload", payload))
        )

    def relay_client_callbacks(self) -> RelayClientCallbacks:
        return RelayClientCallbacks(
            mqtt_state_change_callback=self.mqtt_state_change_callback,
            mqtt_message_received_callback=self.mqtt_receipt_callback,
            relay_state_change_callback=self.relay_state_change_callback,
            relay_config_change_callback=self.relay_config_change_callback,
            layout_callback=self.layout_callback,
            snapshot_callback=self.snapshot_callback,
        )

    def relay_state_change_callback(self, changes: dict[str, ObservedRelayStateChange]) -> None:
        self.post_message(Relays.RelayStateChange(changes))

    def relay_config_change_callback(self, changes: dict[str, RelayConfigChange]) -> None:
        self.post_message(Relays.ConfigChange(changes))

    def layout_callback(self, layout: LayoutLite) -> None:
        self.post_message(Relays.Layout(layout))

    def snapshot_callback(self, snapshot: SnapshotSpaceheat) -> None:
        self.post_message(Relays.Snapshot(snapshot))

    def mqtt_state_change_callback(self, old_state: str, new_state: str) -> None:
        self.post_message(Mqtt.StateChange(old_state, new_state))

    def mqtt_receipt_callback(self, topic: str, payload: bytes) -> None:
        self.post_message(Mqtt.Receipt(topic, payload))

