from typing import Any
import dotenv
from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.containers import Vertical
import asyncio
import uuid
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage
from gwproto import Message
from gwproto.named_types import AdminWakesUp
from gw_spaceheat.admin.base_client import BaseAdmin
from admin.settings import AdminClientSettings

class Admin(BaseAdmin):
    
    def __init__(self, settings: AdminClientSettings):
        super().__init__(settings=settings, user="admin", json=False)
        self.state = "Dormant"  # Initial state
        self.message_queue = asyncio.Queue()

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        with Vertical():
            yield Static("Relay States", id="relay_states")
            yield Input(placeholder="Pick relay number or 'E' for exit", id="user_input")

    def on_mount(self) -> None:
        """Setup tasks when the app starts."""
        # Start MQTT message processing
        self.call_later(self.process_messages)

    async def process_messages(self) -> None:
        """Process MQTT messages and update the UI."""
        while True:
            message = await self.message_queue.get()
            relay_states_widget = self.query_one("#relay_states", Static)
            relay_states_widget.update(f"Current State: {self.state}\nLast Message: {message}")

    def send_mqtt_message(self, user_input: str) -> None:
        """Send an MQTT message based on user input."""
        if self.state == "Dormant":
            message = Message[AdminWakesUp](
                Src="admin",
                Dst="scada",
                MessageId=str(uuid.uuid4()),
                Payload=AdminWakesUp(FromName="admin", ToName="scada"),
            )
            print(f"About to publish {message.mqtt_topic()}")
            self.client.publish(
                topic=message.mqtt_topic(),
                payload=message.model_dump_json().encode(),
            )
            self.state = "Active"

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle user input."""
        user_input = event.value.strip()
        if user_input.upper() == "E":
            self.exit("Exiting...")
        else:
            print("About to send message")
            self.send_mqtt_message(user_input)
            # Clear input after processing
            input_widget = self.query_one("#user_input", Input)
            input_widget.value = ""

    def on_message(self, _: Any, __: Any, message: MQTTMessage) -> None:
        payload = self.payload_from_mqtt(message)
        # asyncio.run_coroutine_threadsafe(
        #     self.message_queue.put(payload), asyncio.get_running_loop()
        # )
        try:
            future = asyncio.run_coroutine_threadsafe(self.message_queue.put(payload), self._loop)
            future.result()
        except Exception as e:
            print(f"Failed to add message to queue: {e}")

    async def run_admin_async(self) -> None:
        """Run the app asynchronously."""

        self.client.connect(self.mqtt_config.host, port=self.mqtt_config.effective_port())
        self.client.loop_start()
        print("started MQTT in background")
        try:
            await self.run()  # Start the Textual app
        finally:
            self.client.loop_stop()
    



# MQTT Client setup
settings = AdminClientSettings(_env_file=dotenv.find_dotenv())
app = Admin(settings)
app.run()
