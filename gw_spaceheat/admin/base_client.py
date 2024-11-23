import ssl
import sys
import uuid
from textual.app import App
from enum import StrEnum, auto
from typing import Any
import dotenv
from gwproto.data_classes.house_0_layout import House0Layout
from actors.config import ScadaSettings
import rich
from gwproactor.config import MQTTClient
from gwproto import Message, MQTTTopic
from gwproto.data_classes.house_0_names import H0N
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessage
from gwproto.named_types import AdminWakesUp, FsmEvent, MachineStates
from admin.settings import AdminClientSettings


class AppState(StrEnum):
    not_started = auto()
    awaiting_connect = auto()
    awaiting_suback = auto()
    awaiting_command_ack = auto()
    awaiting_report = auto()
    stopped = auto()


class BaseAdmin(App):
    #CSS_PATH = "styles.css"
    client: PahoMQTTClient
    settings: AdminClientSettings
    user: str
    json: bool
    comm_state: AppState

    def __init__(
        self,
        *,
        settings: AdminClientSettings,
        user: str,
        json: bool,
    ) -> None:
        super().__init__()
        dotenv_file = dotenv.find_dotenv()
        scada_settings = ScadaSettings(_env_file=dotenv_file)
        self.layout = House0Layout.load(scada_settings.paths.hardware_layout)
        self.settings = settings
        self.user = user
        self.json = json
        self.command_message_id = ""
        self.comm_state = AppState.not_started
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

    # def run(self) -> None:
    #     if not self.json:
    #         rich.print(f"Connecting to broker at <{self.mqtt_config.host}>")
    #     self.comm_state = AppState.awaiting_connect
    #     self.client.connect(
    #         self.mqtt_config.host, port=self.mqtt_config.effective_port()
    #     )
    #     self.client.loop_forever()
    @property
    def mqtt_config(self) -> MQTTClient:
        return self.settings.link

    def on_connect(self, _: Any, _userdata: Any, _flags: dict, _rc: int) -> None:
        topic = MQTTTopic.encode(
            envelope_type=Message.type_name(),
            src=H0N.primary_scada, # self.settings.target_gnode,
            dst=H0N.admin,
            message_type="#",
        )
        self.comm_state = AppState.awaiting_suback
        if not self.json:
            rich.print(f"Connected. Subscribing to <{topic}>")
        self.client.subscribe(topic=topic)

    def on_subscribe(
        self, _: Any, _userdata: Any, _mid: int, _granted_qos: list[int]
    ) -> None:
        self.comm_state = AppState.awaiting_command_ack

    def on_connect_fail(self, _: Any, _userdata: Any) -> None:
        if not self.json:
            rich.print("Connect failed. Exiting")
        self.comm_state = AppState.stopped
        self.client.loop_stop()
        sys.exit(1)

    def on_disconnect(self, _: Any, _userdata: Any, _rc: int) -> None:
        if not self.json:
            rich.print("Disconnected. Exiting")
        self.comm_state = AppState.stopped
        self.client.loop_stop()
        sys.exit(2)
    
    

    def on_message(self, _: Any, _userdata: Any, message: MQTTMessage) -> None:
        raise NotImplementedError

    def payload_from_mqtt(self, message: MQTTMessage) -> AdminWakesUp:
        msg_type = message.topic.split("/")[-1].replace("-", ".")
        if msg_type == AdminWakesUp.model_fields["TypeName"].default:
            return Message[AdminWakesUp].model_validate_json(message.payload).Payload
        elif msg_type == FsmEvent.model_fields["TypeName"].default:
            return Message[FsmEvent].model_validate_json(message.payload).Payload
        elif msg_type == MachineStates.model_fields["TypeName"].default:
            return Message[MachineStates].model_validate_json(message.payload).Payload
        else:
            raise Exception(f"Need to add {msg_type} to payload_from_mqtt!")