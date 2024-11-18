from typing import Any
import asyncio
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
        self.msg = message
        msg_type = message.topic.split("/")[-1].replace("-", ".")
        print(f"Just got {msg_type}")


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

class KridaUI:
    def __init__(self):
        self._stop_requested = False

    async def krida_ui(self):
        while not self._stop_requested:
            i = await async_input("Pick relay number or 'E' for exit\n")
            if i == 'E':
                print("Exiting...")
                self._stop_requested = True
            else:
                print(f"You entered: {i}")