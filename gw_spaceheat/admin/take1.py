# Got messages back and forth with SCADA
# Got async input to work on its own, and to trigger message to SCADA
# Did not get screen to refresh with new data while also getting async input
# Next up: try two different windows in textual.
import uuid
from typing import Any
import asyncio
from asyncio import run_coroutine_threadsafe
import rich
from gwproto import Message
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage
from admin.base_client import AppState
from admin.base_client import BaseAdmin
from admin.settings import AdminClientSettings
from gwproto.named_types import AdminWakesUp, MachineStates
from transitions import Machine

async def async_input(prompt: str, timeout: float = 1.0) -> str | None:
    loop = asyncio.get_event_loop()
    try:
        # Run input in a separate thread with a timeout
        return await asyncio.wait_for(loop.run_in_executor(None, input, prompt), timeout=timeout)
    except asyncio.TimeoutError:
        return None
    #return await loop.run_in_executor(None, input, prompt)


class WatchAdminClient(BaseAdmin):
    node: ShNode
    client: PahoMQTTClient
    settings: AdminClientSettings
    states = ["Dormant", "Active"]
    transitions = [
        {"trigger": "GoLive", "source": "Dormant", "dest": "Active"},
        {"trigger": "TimedOut", "source": "Active", "dest": "Dormant"}
         ]

    def __init__(
        self,
        settings: AdminClientSettings,
    ) -> None:
        super().__init__(settings=settings, user="admin_user", json=False
        )
        self.node = self.layout.node(H0N.admin)
        self._stop_requested = False
        self._received_messages = asyncio.Queue()
        self.first_run = True
        self.machine = Machine(
            model=self,
            states=WatchAdminClient.states,
            transitions=WatchAdminClient.transitions,
            initial="Dormant",
            send_event=False,
        )

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.comm_state = AppState.awaiting_command_ack


    def on_message(self, _: Any, _userdata: Any, message: MQTTMessage) -> None:
        payload = self.payload_from_mqtt(message)
        try:
            future = run_coroutine_threadsafe(self._received_messages.put(payload), self._loop)
            future.result()  # Wait for the operation to complete
            #print("Message successfully added to queue")
        except Exception as e:
            print(f"Failed to add message to queue: {e}")
        
    async def process_messages(self):
        while not self._stop_requested:
            message = await self._received_messages.get()
            print(f"Message dequeued: {message.TypeName}")
            match message:
                case AdminWakesUp():
                    print("Got AdminWakesUp")
                    if self.state == "Dormant":
                        self.GoLive()
                    print(f"My state is {self.state}")
                        # This changes the state. We want 
                        # it reflected in the ui

    async def handle_ui(self):
        while not self._stop_requested:
            print("\033[H\033[J", end="")
            print(f"State: {self.state}")
            self.first_run = False
    
            user_input = await async_input("Pick relay number or 'E' for exit\n", 1)
            if user_input is None:
                # No input received; continue looping
                continue
            elif user_input.strip().upper() == 'E':
                print("Exiting...")
                self._stop_requested = True
            else:
                print(f"You entered: {user_input}")
                if self.state == "Dormant":
                    message = Message[AdminWakesUp](
                        Src=H0N.admin,
                        Dst=self.layout.scada_g_node_alias,
                        MessageId=str(uuid.uuid4()),
                        Payload=AdminWakesUp(
                            FromName=H0N.admin,
                            ToName=H0N.primary_scada
                        )
                    )
                    self.client.publish(
                        topic=message.mqtt_topic(),
                        payload=message.model_dump_json().encode()
                    )

    
    async def run_async(self):
        self._loop = asyncio.get_running_loop()
        self.client.connect(self.mqtt_config.host, port=self.mqtt_config.effective_port())
        self.client.loop_start()  # Start the MQTT client loop in the background
        tasks = [self.process_messages(), self.handle_ui()]
        try:
            await asyncio.gather(*tasks)
        finally:
            self.client.loop_stop()
    
    def run(self) -> None:
        """Override run to integrate asyncio."""
        asyncio.run(self.run_async())

