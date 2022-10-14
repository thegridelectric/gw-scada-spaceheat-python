"""Message structures for use between proactor and its sub-objects."""
import uuid
import time
from enum import Enum
from typing import Any, Optional, TypeVar, Generic, Dict, List, Literal, Mapping

from paho.mqtt.client import MQTTMessage
from pydantic import BaseModel, Field, validator
from pydantic.fields import FieldInfo
from pydantic.generics import GenericModel

EnumType = TypeVar("EnumType")


def as_enum(value: Any, enum_type: EnumType, default: Optional[EnumType] = None) -> Optional[EnumType]:
    try:
        return enum_type(value)
    except ValueError:
        return default


class MessageType(Enum):
    invalid = "invalid"
    mqtt_subscribe = "mqtt_subscribe"
    mqtt_message = "mqtt_message"

    mqtt_connected = "mqtt_connected"
    mqtt_disconnected = "mqtt_disconnected"
    mqtt_connect_failed = "mqtt_connect_failed"

    mqtt_suback = "mqtt_suback"

    event_report = "event_report"

class KnownNames(Enum):
    proactor = "proactor"
    mqtt_clients = "mqtt_clients"


class Header(BaseModel):
    src: str
    dst: str = ""
    message_type: str
    message_id: str = ""
    type_name: str = Field("gridworks.header.000", const=True)

PayloadT = TypeVar("PayloadT")

class Message(GenericModel, Generic[PayloadT]):
    header: Header
    payload: PayloadT
    type_name: str = Field("gridworks.message.000", const=True)

    def __init__(self, **kwargs):
        kwargs["header"] = self._header_from_kwargs(kwargs)
        super().__init__(**kwargs)

    def mqtt_topic(self):
        return f"{self.header.src}/{self.type_name.replace('.', '-')}"

    @classmethod
    def _header_from_kwargs(cls, kwargs: dict) -> Header:
        header_kwargs = dict()
        payload = kwargs["payload"]
        for header_field, payload_fields in [
            ("src", ["src"]),
            ("dst", ["dst"]),
            ("message_id", ["message_id"]),
            ("message_type", ["type_name", "type_alias", "TypeAlias"]),
        ]:
            val = kwargs.get(header_field, None)
            if val is None:
                for payload_field in payload_fields:
                    if hasattr(payload, payload_field):
                        val = getattr(payload, payload_field)
                    elif isinstance(payload, Mapping) and payload_field in payload:
                        val = payload[payload_field]
            if val is not None:
                header_kwargs[header_field] = val
        header = kwargs.get("header", None)
        if header is None:
            header = Header(**header_kwargs)
        else:
            header = header.copy(update=header_kwargs, deep=True)
        return header

class MQTTClientsPayload(BaseModel):
    client_name: str
    userdata: Optional[Any]


MQTTClientsPayloadT = TypeVar("MQTTClientsPayloadT", bound=MQTTClientsPayload)


class MQTTClientMessage(Message[MQTTClientsPayloadT], Generic[MQTTClientsPayloadT]):
    def __init__(
        self,
        message_type: MessageType,
        payload: MQTTClientsPayloadT,
    ):
        super().__init__(
            header=Header(
                src=KnownNames.mqtt_clients.value,
                dst=KnownNames.proactor.value,
                message_type=message_type.value,
            ),
            payload=payload,
        )


class MQTTMessageModel(BaseModel):
    timestamp: float = 0
    state: int = 0
    dup: bool = False
    mid: int = 0
    topic: str = ""
    payload: bytes = bytes()
    qos: int = 0
    retain: bool = False

    @classmethod
    def from_mqtt_message(cls, message: MQTTMessage) -> "MQTTMessageModel":
        model = MQTTMessageModel()
        for field_name in model.__fields__:
            setattr(model, field_name, getattr(message, field_name))
        return model


class MQTTReceiptPayload(MQTTClientsPayload):
    message: MQTTMessageModel


class MQTTReceiptMessage(MQTTClientMessage[MQTTReceiptPayload]):
    def __init__(
        self,
        client_name: str,
        userdata: Optional[Any],
        message: MQTTMessage,
    ):
        super().__init__(
            message_type=MessageType.mqtt_message,
            payload=MQTTReceiptPayload(
                client_name=client_name,
                userdata=userdata,
                message=MQTTMessageModel.from_mqtt_message(message),
            ),
        )


class MQTTSubackPayload(MQTTClientsPayload):
    mid: int
    granted_qos: List[int]
    num_pending_subscriptions: int


class MQTTSubackMessage(MQTTClientMessage[MQTTSubackPayload]):
    def __init__(
        self,
        client_name: str,
        userdata: Optional[Any],
        mid: int,
        granted_qos: List[int],
        num_pending_subscriptions: int,
    ):
        super().__init__(
            message_type=MessageType.mqtt_suback,
            payload=MQTTSubackPayload(
                client_name=client_name,
                userdata=userdata,
                mid=mid,
                granted_qos=granted_qos,
                num_pending_subscriptions=num_pending_subscriptions,
            ),
        )


class MQTTCommEventPayload(MQTTClientsPayload):
    rc: int


class MQTTConnectPayload(MQTTCommEventPayload):
    flags: Dict


class MQTTConnectMessage(MQTTClientMessage[MQTTConnectPayload]):
    def __init__(
        self,
        client_name: str,
        userdata: Optional[Any],
        flags: Dict,
        rc: int,
    ):
        super().__init__(
            message_type=MessageType.mqtt_connected,
            payload=MQTTConnectPayload(
                client_name=client_name,
                userdata=userdata,
                flags=flags,
                rc=rc,
            ),
        )


class MQTTConnectFailPayload(MQTTClientsPayload):
    pass


class MQTTConnectFailMessage(MQTTClientMessage[MQTTConnectFailPayload]):
    def __init__(self, client_name: str, userdata: Optional[Any]):
        super().__init__(
            message_type=MessageType.mqtt_connect_failed,
            payload=MQTTConnectFailPayload(
                client_name=client_name,
                userdata=userdata,
            ),
        )


class MQTTDisconnectPayload(MQTTCommEventPayload):
    pass


class MQTTDisconnectMessage(MQTTClientMessage[MQTTDisconnectPayload]):
    def __init__(self, client_name: str, userdata: Optional[Any], rc: int):
        super().__init__(
            message_type=MessageType.mqtt_disconnected,
            payload=MQTTDisconnectPayload(
                client_name=client_name,
                userdata=userdata,
                rc=rc,
            ),
        )


def type_name(s: str, version: str = "000", **kwargs) -> FieldInfo:
    kwargs.pop("const", None)
    return Field(f"{s}.{version}", const=True, **kwargs)


class EventBase(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_ns: int = Field(default_factory=time.time_ns)
    src: str = ""
    type_name: str = Field(const=True)


EventT = TypeVar("EventT", bound=EventBase)


class StartupEvent(EventBase):
    clean_shutdown: bool
    type_name: Literal["gridworks.event.startup.000"] = "gridworks.event.startup.000"


class ShutdownEvent(EventBase):
    reason: str
    type_name: Literal["gridworks.event.shutdown.000"] = "gridworks.event.shutdown.000"


class Problems(Enum):
    error = "error"
    warning = "warning"


class ProblemEvent(EventBase):
    problem_type: Problems
    summary: str
    details: str = ""
    type_name: Literal["gridworks.event.problem.000"] = "gridworks.event.problem.000"

    @validator("problem_type", pre=True)
    def problem_type_value(cls, v):
        return as_enum(v, Problems)


class CommEvent(EventBase):
    ...


class MQTTCommEvent(CommEvent):
    ...


class MQTTConnectFailedEvent(MQTTCommEvent):
    type_name: Literal["gridworks.event.comm.mqtt.connect_failed.000"] = "gridworks.event.comm.mqtt.connect_failed.000"


class MQTTDisconnectEvent(MQTTCommEvent):
    type_name: Literal["gridworks.event.comm.mqtt.disconnect.000"] = "gridworks.event.comm.mqtt.disconnect.000"


class MQTTFullySubscribedEvent(CommEvent):
    type_name: Literal["gridworks.event.comm.mqtt.fully_subscribed.000"] = "gridworks.event.comm.mqtt.fully_subscribed.000"


class EventMessage(Message[EventT], Generic[EventT]):
    ...


class Ack(BaseModel):
    acks_message_id: str = ""
    type_name: Literal["gridworks.ack.000"] = "gridworks.ack.000"
