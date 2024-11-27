from typing import Any

import rich
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage

from admin.base_client import AppState
from admin.base_client import BaseAdminClient
from admin.settings import AdminClientSettings

class WatchAdminClient(BaseAdminClient):
    client: PahoMQTTClient
    settings: AdminClientSettings
    command_message_id: str

    def __init__(
        self,
        *,
        settings: AdminClientSettings,
        user: str,
        json: bool,
    ) -> None:
        super().__init__(
            settings=settings,
            user=user,
            json=json
        )
        self.command_message_id = ""

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.state = AppState.awaiting_command_ack


    def on_message(self, _: Any, _userdata: Any, message: MQTTMessage) -> None:
        if not self.json:
            rich.print(f"Received <{message.topic}>  in state <{self.state}>")
