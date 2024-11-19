from typing import Any
import asyncio
import rich
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage

from admin.base_client import AppState
from admin.base_client import BaseAdminClient
from admin.settings import AdminClientSettings


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


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
        super().__init__(settings=settings, user=user, json=json
        )
        self.command_message_id = ""
        self._stop_requested = False
        self._received_messages = asyncio.Queue()

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.state = AppState.awaiting_command_ack


    def on_message(self, _: Any, _userdata: Any, message: MQTTMessage) -> None:
        if not self.json:
            rich.print(f"Received <{message.topic}>  in state <{self.state}>")
        msg_type = message.topic.split("/")[-1].replace("-", ".")
        asyncio.create_task(self._received_messages.put(message))
        print(f"Just got {msg_type}")
    
    async def process_messages(self):
        while not self._stop_requested:
            message = await self._received_messages.get()
            msg_type = message.topic.split("/")[-1].replace("-", ".")
            print(f"Processing received message: {msg_type}")

    async def handle_ui(self):
        while not self._stop_requested:
            user_input = await async_input("Pick relay number or 'E' for exit\n")
            if user_input.strip().upper()  == 'E':
                print("Exiting...")
                self._stop_requested = True
            else:
                print(f"You entered: {user_input}")
                # Here, you can send the input as an MQTT message if needed
                # self.client.publish("your/topic", payload=user_input)
    
    async def run_async(self):
        self.client.loop_start()  # Start the MQTT client loop in the background
        tasks = [self.process_messages(), self.handle_ui()]
        try:
            await asyncio.gather(*tasks)
        finally:
            self.client.loop_stop()
    
    def run(self) -> None:
        """Override run to integrate asyncio."""
        asyncio.run(self.run_async())

