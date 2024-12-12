from textual.messages import Message

from textual.widget import Widget

from admin.watch.widgets.constrained_mqtt_widget import Mqtt


class AdminClientMessagePump(Widget):

    def change_state(self, old_state: str, new_state: str) -> None:
        self.post_message(Mqtt.StateChange(old_state, new_state))

    def mqtt_receipt(self, topic: str, payload: bytes) -> None:
        self.post_message(Mqtt.Receipt(topic, payload))