import platform
import ssl
import sys
import uuid
from enum import StrEnum, auto
from typing import Any

import rich
from gwproactor.config import MQTTClient
from gwproto import Message, MQTTTopic
from gwproto.messages import Ack
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage

from admin.messages import AdminCommandReadRelays
from admin.messages import AdminCommandSetRelay
from admin.messages import AdminInfo
from admin.messages import RelayInfo
from admin.messages import RelayStates
from actors.config import ADMIN_NAME
from admin.settings import AdminClientSettings


class AppState(StrEnum):
    not_started = auto()
    awaiting_connect = auto()
    awaiting_suback = auto()
    awaiting_command_ack = auto()
    awaiting_report = auto()
    stopped = auto()


class MQTTAdmin:
    client: PahoMQTTClient
    settings: AdminClientSettings
    relay_name: str
    closed: bool
    user: str
    json: bool
    command_message_id: str
    state: AppState

    def __init__(
        self,
        *,
        settings: AdminClientSettings,
        relay_name: str,
        closed: bool,
        user: str,
        json: bool,
    ) -> None:
        self.settings = settings
        self.relay_name = relay_name
        self.closed = closed
        self.user = user
        self.json = json
        self.command_message_id = ""
        self.state = AppState.not_started
        self.client = PahoMQTTClient("-".join(str(uuid.uuid4()).split("-")[:-1]))
        self.client.username_pw_set(
            username=self.mqtt_config.username,
            password=self.mqtt_config.password.get_secret_value(),
        )
        tls_config = self.mqtt_config.tls
        if tls_config.use_tls:
            self.client.tls_set(
                ca_certs=tls_config.paths.ca_cert_path,
                certfile=tls_config.paths.cert_path,
                keyfile=tls_config.paths.private_key_path,
                cert_reqs=tls_config.cert_reqs,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
                ciphers=tls_config.ciphers,
                keyfile_password=tls_config.keyfile_password.get_secret_value(),
            )
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_connect_fail = self.on_connect_fail
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe

    def run(self) -> None:
        if not self.json:
            rich.print(f"Connecting to broker at <{self.mqtt_config.host}>")
        self.state = AppState.awaiting_connect
        self.client.connect(
            self.mqtt_config.host, port=self.mqtt_config.effective_port()
        )
        self.client.loop_forever()

    @property
    def mqtt_config(self) -> MQTTClient:
        return self.settings.link

    def on_connect(self, _: Any, _userdata: Any, _flags: dict, _rc: int) -> None:
        topic = MQTTTopic.encode(
            envelope_type=Message.type_name(),
            src=self.settings.target_gnode,
            dst=ADMIN_NAME,
            message_type="#",
        )
        self.state = AppState.awaiting_suback
        if not self.json:
            rich.print(f"Connected. Subscribing to <{topic}>")
        self.client.subscribe(topic=topic)

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.state = AppState.awaiting_command_ack
        message = Message[AdminCommandSetRelay](
            Src=ADMIN_NAME,
            Dst=self.settings.target_gnode,
            MessageId=str(uuid.uuid4()),
            AckRequired=True,
            Payload=AdminCommandSetRelay(
                CommandInfo=AdminInfo(
                    User=self.user,
                    SrcMachine=platform.node(),
                ),
                RelayInfo=RelayInfo(
                    RelayName=self.relay_name,
                    Closed=self.closed,
                ),
            ),
        )
        self.command_message_id = message.Payload.MessageId
        topic = message.mqtt_topic()
        if not self.json:
            rich.print("Subscribed. Sending:")
            rich.print(message)
            rich.print(f"to topic <{topic}>")
        self.client.publish(topic=topic, payload=message.model_dump_json().encode())

    def on_connect_fail(self, _: Any, _userdata: Any) -> None:
        if not self.json:
            rich.print("Connect failed. Exiting")
        self.state = AppState.stopped
        self.client.loop_stop()
        sys.exit(1)

    def on_disconnect(self, _: Any, _userdata: Any, _rc: int) -> None:
        if not self.json:
            rich.print("Disconnected. Exiting")
        self.state = AppState.stopped
        self.client.loop_stop()
        sys.exit(2)

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
                    Src=ADMIN_NAME,
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
