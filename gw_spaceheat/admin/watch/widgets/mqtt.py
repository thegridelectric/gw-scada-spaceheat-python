from textual.messages import Message

from textual.widget import Widget


class Mqtt(Widget):

    class StateChange(Message):

        def __init__(self, old_state: str, new_state: str) -> None:
            self.old_state = old_state
            self.new_state = new_state
            super().__init__()

    class Receipt(Message):

        def __init__(self, topic: str, payload: bytes) -> None:
            self.topic = topic
            self.payload = payload
            super().__init__()

    def change_state(self, old_state: str, new_state: str) -> None:
        self.post_message(Mqtt.StateChange(old_state, new_state))

    def mqtt_receipt(self, topic: str, payload: bytes) -> None:
        self.post_message(Mqtt.Receipt(topic, payload))
