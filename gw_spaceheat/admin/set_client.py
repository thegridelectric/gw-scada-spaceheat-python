import platform
import time
import sys
import uuid
from typing import Any

import rich
from gwproto import Message
from gwproto.enums import ChangeRelayState
from gwproto.data_classes.house_0_names import H0N
from gwproto.messages import Ack
from gwproto.named_types import FsmEvent
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage

from admin.base_client import AppState
from admin.base_client import BaseAdminClient
from admin.messages import AdminCommandReadRelays
from admin.messages import AdminInfo
from admin.messages import RelayStates
from admin.settings import AdminClientSettings

class SetAdminClient(BaseAdminClient):
    client: PahoMQTTClient
    settings: AdminClientSettings
    open_relay: bool
    command_message_id: str

    def __init__(
        self,
        *,
        settings: AdminClientSettings,
        open_relay: bool,
        user: str,
        json: bool,
    ) -> None:
        super().__init__(
            settings=settings,
            user=user,
            json=json
        )
        self.open_relay = open_relay
        self.command_message_id = ""

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.state = AppState.awaiting_command_ack
        event_name = ChangeRelayState.CloseRelay
        if self.open_relay:
            event_name = ChangeRelayState.OpenRelay
        event = FsmEvent(
            FromHandle=H0N.admin,
            ToHandle=f"{H0N.admin}.{H0N.vdc_relay}",
            EventType=ChangeRelayState.enum_name(),
            EventName=event_name,
            SendTimeUnixMs=int(time.time() * 1000),
            TriggerId=str(uuid.uuid4())
        )
        message = Message(
            Src=H0N.admin,
            Dst=self.settings.target_gnode,
            MessageId=event.TriggerId,
            Payload=event,
        )
        self.command_message_id = event.TriggerId
        topic = message.mqtt_topic()
        if not self.json:
            rich.print("Subscribed. Sending:")
            rich.print(message)
            rich.print(f"to topic <{topic}>")
        self.client.publish(topic=topic, payload=message.model_dump_json().encode())

    def on_message(self, _: Any, _userdata: Any, message: MQTTMessage) -> None:
        if not self.json:
            rich.print(f"Received <{message.topic}>  in state <{self.state}>")
        msg_type = message.topic.split("/")[-1].replace("-", ".")
        if (
            self.state == AppState.awaiting_command_ack
            and msg_type == Ack.model_fields["TypeName"].default
        ):
            ack_message = Message[Ack].model_validate_json(message.payload)
            if ack_message.Payload.AckMessageID == self.command_message_id:
                self.state = AppState.awaiting_report
                message = Message[AdminCommandReadRelays](
                    Src=H0N.admin,
                    Dst=self.settings.target_gnode,
                    MessageId=str(uuid.uuid4()),
                    AckRequired=True,
                    Payload=AdminCommandReadRelays(
                        CommandInfo=AdminInfo(
                            User=self.user,
                            SrcMachine=platform.node(),
                        ),
                    ),
                )
                self.command_message_id = message.Payload.MessageId
                topic = message.mqtt_topic()
                if not self.json:
                    rich.print("Subscribed. Sending:")
                    rich.print(message)
                    rich.print(f"at topic <{topic}>")
                self.client.publish(
                    topic=topic, payload=message.model_dump_json().encode()
                )
            else:
                if not self.json:
                    rich.print(
                        "Received unexpected ack for "
                        f"{ack_message.Payload.AckMessageID}. Expected: "
                        f"{self.command_message_id}. Exiting."
                    )
                self.state = AppState.stopped
                self.client.loop_stop()
                sys.exit(3)
        elif (
            self.state == AppState.awaiting_report
            and msg_type == RelayStates.model_fields["TypeName"].default
        ):
            report_message = Message[RelayStates].model_validate_json(message.payload)
            if self.json:
                print(report_message.Payload.model_dump_json(indent=2))  # noqa
            else:
                rich.print(report_message.Payload)
            self.state = AppState.stopped
            self.client.loop_stop()
            sys.exit(0)
