import asyncio
import datetime
import enum
import inspect
import pprint
import socket
import textwrap
import time
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from inspect import getframeinfo
from inspect import stack
from pathlib import Path
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from actors2 import Scada2
from actors.actor_base import ActorBase
from actors.atn import Atn
from actors.cloud_ear import CloudEar
from actors.home_alone import HomeAlone
from actors.scada import Scada
from actors.utils import gw_mqtt_topic_decode
from actors.utils import gw_mqtt_topic_encode
from config import ScadaSettings
from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.components.boolean_actuator_component import BooleanActuatorCac
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.components.electric_meter_component import ElectricMeterCac
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorCac
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from data_classes.components.resistive_heater_component import ResistiveHeaterCac
from data_classes.components.resistive_heater_component import ResistiveHeaterComponent
from data_classes.components.temp_sensor_component import TempSensorCac
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto.message import Message
from proactor.message import MQTTConnectFailPayload
from proactor.message import MQTTConnectPayload
from proactor.message import MQTTDisconnectPayload
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload
from schema.messages import GtDispatchBooleanLocal
from schema.messages import GtShStatus
from schema.messages import GtShStatus_Maker
from schema.messages import SnapshotSpaceheat
from schema.messages import SnapshotSpaceheat_Maker
from schema.messages import GsDispatch
from schema.schema_switcher import TypeMakerByAliasDict


class CommEvents(enum.Enum):
    invalid = "invalid"
    connect = "connect"
    connect_fail = "connect_fail"
    subscribe = "subscribe"
    message = "message"
    mqtt_message = "mqtt_message"
    publish = "publish"
    unsubscribe = "unsubscribe"
    disconnect = "disconnect"
    socket_open = "socket_open"
    socket_close = "socket_close"
    socket_register_write = "socket_register_write"
    socket_unregister_write = "socket_unregister_write"


@dataclass
class CommEvent:
    timestamp: datetime.datetime = field(default_factory=datetime.datetime)
    broker: str = ""
    event: CommEvents = CommEvents.invalid
    params: List = field(default_factory=list)

    def __str__(self):
        param_str = str(self.params)
        max_param_width = 80
        if len(param_str) > max_param_width:
            param_str = param_str[:max_param_width] + "..."
        return f"{self.timestamp.isoformat()}  {self.broker:14s}  {self.event.value:23s}  {param_str}"


def wait_for(
    f: Callable[[], bool],
    timeout: float,
    tag: str = "",
    raise_timeout: bool = True,
    retry_duration: float = 0.1,
) -> bool:
    """Call function f() until it returns True or a timeout is reached. retry_duration specified the sleep time between
    calls. If the timeout is reached before f return True, the function will either raise a ValueError (the default),
    or, if raise_timeout==False, it will return False. Function f is guaranteed to be called at least once. If an
    exception is raised the tag string will be attached to its message.
    """
    now = time.time()
    until = now + timeout
    if now >= until:
        if f():
            return True
    while now < until:
        if f():
            return True
        now = time.time()
        if now < until:
            time.sleep(min(retry_duration, until - now))
            now = time.time()
    if raise_timeout:
        raise ValueError(
            f"ERROR. "
            f"[{tag}] wait_for() timed out after {timeout} seconds, wait function {f}"
        )
    else:
        return False


Predicate = Callable[[], bool]
AwaitablePredicate = Callable[[], Awaitable[bool]]
ErrorStringFunction = Callable[[], str]


async def await_for(
    f: Union[Predicate, AwaitablePredicate],
    timeout: float,
    tag: str = "",
    raise_timeout: bool = True,
    retry_duration: float = 0.1,
    err_str_f: Optional[ErrorStringFunction] = None,
) -> bool:
    """Similar to wait_for(), but awaitable. Instead of sleeping after a False resoinse from function f, await_for
    will asyncio.sleep(), allowing the event loop to continue. Additionally, f may be either a function or a coroutine.
    """
    now = start = time.time()
    until = now + timeout
    err_format = (
        "ERROR. [{tag}] wait_for() timed out after {seconds} seconds\n"
        "  [{tag}]\n"
        "  From {file}:{line}\n"
        "  wait function: {f}"
        "{err_str}"
    )
    if err_str_f is not None:
        def err_str_f_() -> str:
            return "\n" + textwrap.indent(err_str_f(), "  ")
    else:
        def err_str_f_() -> str:
            return ""
    f_is_async = inspect.iscoroutinefunction(f)
    result = False
    if now >= until:
        if f_is_async:
            result = await f()
        else:
            result = f()
    while now < until and result is False:
        if f_is_async:
            result = await f()
        else:
            result = f()
        if result is False:
            now = time.time()
            if now < until:
                await asyncio.sleep(min(retry_duration, until - now))
                now = time.time()
    if result is True:
        return True
    else:
        if raise_timeout:
            caller = getframeinfo(stack()[1][0])
            raise ValueError(
                err_format.format(
                    tag=tag,
                    file=Path(caller.filename).name,
                    line=caller.lineno,
                    seconds=time.time() - start,
                    f=f,
                    err_str=err_str_f_()
                )
            )
        else:
            return False


def flush_components():
    BooleanActuatorComponent.by_id = {}
    ElectricMeterComponent.by_id = {}
    PipeFlowSensorComponent.by_id = {}
    ResistiveHeaterComponent.by_id = {}
    TempSensorComponent.by_id = {}
    Component.by_id = {}


def flush_cacs():
    BooleanActuatorCac.by_id = {}
    ElectricMeterCac.by_id = {}
    PipeFlowSensorCac.by_id = {}
    ResistiveHeaterCac.by_id = {}
    TempSensorCac.by_id = {}
    ComponentAttributeClass.by_id = {}


def flush_spaceheat_nodes():
    ShNode.by_id = {}


def flush_all():
    flush_components()
    flush_cacs()
    flush_spaceheat_nodes()


class AbstractActor(ActorBase):
    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super().__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)

    def subscriptions(self):
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def main(self):
        pass


class AtnRecorder(Atn):
    snapshot_received: int
    status_received: int
    latest_snapshot_payload: Optional[SnapshotSpaceheat]
    latest_status_payload: Optional[GtShStatus]
    num_received: int
    num_received_by_topic: Dict[str, int]

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.snapshot_received = 0
        self.status_received = 0
        self.latest_snapshot_payload: Optional[SnapshotSpaceheat] = None
        self.latest_status_payload: Optional[GtShStatus] = None
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        super().__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)

    def on_gw_mqtt_message(self, client, userdata, message):

        old_num_received = self.num_received
        self.num_received += 1
        _, type_alias = gw_mqtt_topic_decode(message.topic).split("/")
        self.logger.info(
            f"type_alias: [{type_alias}] present in {self.decoders.types()}? {type_alias in self.decoders.types()}")
        if type_alias not in TypeMakerByAliasDict.keys():
            topic = self.decoders.decode_str(type_alias, message.payload).header.message_type
        else:
            topic = message.topic
        old_num_received_by_topic = self.num_received_by_topic[topic]
        self.num_received_by_topic[topic] += 1
        self.logger.info(
            f"AtnRecorder.on_gw_mqtt_message ({topic}: "
            f"{old_num_received} -> {self.num_received})  "
            f"{old_num_received_by_topic} -> {self.num_received_by_topic[topic]}"
        )
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        if isinstance(payload, SnapshotSpaceheat):
            self.snapshot_received += 1
            self.latest_snapshot_payload = payload
        if isinstance(payload, GtShStatus):
            self.status_received += 1
            self.latest_status_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self) -> str:
        """Summarize results in a string"""

        # snapshot_received: int
        # status_received: int
        # latest_snapshot_payload: Optional[SnapshotSpaceheat]
        # latest_status_payload: Optional[GtShStatus]
        # num_received: int
        # num_received_by_topic: Dict[str, int]

        s = (
            f"AtnRecorder [{self.node.alias}] total: {self.num_received}  "
            f"status:{self.status_received}  snapshot:{self.snapshot_received}\n"
            "\tnum_received_by_topic:\n"
        )
        for topic in sorted(self.num_received_by_topic.keys()):
            s += f"\t\t{topic:70s}  {self.num_received_by_topic[topic]:2d}\n"
        return s

class HomeAloneRecorder(HomeAlone):
    status_received: int
    latest_status_payload: Optional[GtShStatus]

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.status_received = 0
        self.latest_status_payload: Optional[GtShStatus] = None
        super().__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShStatus):
            self.status_received += 1
            self.latest_status_payload = payload
        super().on_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        return (
            f"HomeAloneRecorder [{self.node.alias}] status_received: {self.status_received}  "
            f"latest_status_payload: {self.latest_status_payload}"
        )


class EarRecorder(CloudEar):
    num_received: int
    num_received_by_topic: Dict[str, int]
    latest_payload: Optional[Any]
    payloads: List[Any]

    def __init__(self, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.latest_payload = None
        self.payloads = []
        super().__init__(settings=settings, hardware_layout=hardware_layout)

    def on_gw_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
        self.payloads.append(payload)
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        s = f"EarRecorder  num_received: {self.num_received}  latest_payload: {self.latest_payload}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n\t{self.num_received_by_topic[topic]:3d}: [{topic}]"
        return s


class ScadaRecorder(Scada):
    """Record data about a PrimaryScada execution during test"""

    num_received_by_topic: Dict[str, int]
    comm_events: List[CommEvent]
    comm_event_counts: Dict[CommEvents, int]

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.num_received_by_topic = defaultdict(int)
        self.comm_events = []
        self.comm_event_counts = defaultdict(int)
        super().__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)
        self.gw_client.on_subscribe = self.on_gw_subscribe
        self.gw_client.on_publish = self.on_gw_publish
        self.gw_client.on_unsubscribe = self.on_gw_unsubscribe
        self.gw_client.on_socket_open = self.on_gw_socket_open
        self.gw_client.on_socket_close = self.on_gw_socket_close
        # on_socket_register_write AND on_socket_unregister_write callbacks are meant for
        # integration with event loops external to paho. They are also noisy, so we don't
        # use them here.

    @property
    def status_topic(self) -> str:
        return gw_mqtt_topic_encode(f"{self.scada_g_node_alias}/{GtShStatus_Maker.type_alias}")

    @property
    def snapshot_topic(self) -> str:
        return gw_mqtt_topic_encode(f"{self.scada_g_node_alias}/{SnapshotSpaceheat_Maker.type_alias}")

    @property
    def last_5_cron_s(self):
        return self._last_5_cron_s

    @last_5_cron_s.setter
    def last_5_cron_s(self, s: int):
        self._last_5_cron_s = s

    @property
    def num_received(self) -> int:
        return self.comm_event_counts[CommEvents.message]

    def _record_comm_event(self, broker: str, event: CommEvents, *params: Any):
        self.comm_event_counts[event] += 1
        self.comm_events.append(
            CommEvent(
                datetime.datetime.now(), broker=broker, event=event, params=list(params)
            )
        )

    @classmethod
    def _socket_str(cls, sock: socket.socket) -> str:
        # noinspection PyBroadException
        try:
            s = f"Socket {sock.fileno()}  {sock.getsockname()}  {sock.getpeername()}"
        except:
            s = str(sock)
        return s

    def on_mqtt_message(self, client, userdata, message):
        self._record_comm_event("local", CommEvents.message, userdata, message)
        self.num_received_by_topic[message.topic] += 1
        super().on_mqtt_message(client, userdata, message)

    def on_gw_mqtt_message(self, client, userdata, message):
        self._record_comm_event("gridworks", CommEvents.message, userdata, message)
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_connect(self, client, userdata, flags, rc):
        self._record_comm_event("gridworks", CommEvents.connect, userdata, flags, rc)
        super().on_gw_connect(client, userdata, flags, rc)

    def on_gw_connect_fail(self, client, userdata, rc):
        self._record_comm_event("gridworks", CommEvents.connect_fail, userdata, rc)
        super().on_gw_connect_fail(client, userdata, rc)

    def on_gw_disconnect(self, client, userdata, rc):
        self._record_comm_event("gridworks", CommEvents.disconnect, userdata, rc)
        super().on_gw_disconnect(client, userdata, rc)

    def on_gw_publish(self, _, userdata, mid):
        self._record_comm_event("gridworks", CommEvents.publish, userdata, mid)

    def on_gw_subscribe(self, _, userdata, mid, granted_qos):
        self._record_comm_event(
            "gridworks", CommEvents.subscribe, userdata, mid, granted_qos
        )

    def on_gw_unsubscribe(self, _, userdata, mid):
        self._record_comm_event("gridworks", CommEvents.unsubscribe, userdata, mid)

    def on_gw_socket_open(self, _, userdata, sock):
        self._record_comm_event(
            "gridworks", CommEvents.socket_open, userdata, self._socket_str(sock)
        )

    def on_gw_socket_close(self, _, userdata, sock):
        self._record_comm_event(
            "gridworks", CommEvents.socket_close, userdata, self._socket_str(sock)
        )

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        pass

    def gt_dispatch_boolean_local_received(self, payload: GtDispatchBooleanLocal):
        pass

    def summary_str(self):
        """Summarize results in a string"""
        s = f"ScadaRecorder  {self.node.alias}  num_received: {self.num_received}  comm events: {len(self.comm_events)}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n  {self.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.comm_event_counts:
            s += f"\n{textwrap.indent(pprint.pformat(self.comm_event_counts), '  ')}"
        if self.comm_events:
            s += "\n  Comm events:"
            for comm_event in self.comm_events:
                s += f"\n    {comm_event}"
        return s


class Scada2Recorder(Scada2):

    suppress_status: bool
    num_received_by_topic: Dict[str, int]
    num_received_by_type: Dict[str, int]
    comm_events: List[CommEvent]
    comm_event_counts: Dict[CommEvents, int]

    def __init__(self, name: str, settings: ScadaSettings, hardware_layout: HardwareLayout, actor_nodes: Optional[List[ShNode]] = None):
        self.num_received_by_topic = defaultdict(int)
        self.num_received_by_type = defaultdict(int)
        self.comm_events = []
        self.comm_event_counts = defaultdict(int)
        self.suppress_status = False
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout, actor_nodes=actor_nodes)

    def time_to_send_status(self) -> bool:
        return not self.suppress_status and super().time_to_send_status()

    @property
    def status_topic(self) -> str:
        return gw_mqtt_topic_encode(f"{self._layout.scada_g_node_alias}/{GtShStatus_Maker.type_alias}")

    @property
    def snapshot_topic(self) -> str:
        return gw_mqtt_topic_encode(f"{self._layout.scada_g_node_alias}/{SnapshotSpaceheat_Maker.type_alias}")

    @property
    def num_received(self) -> int:
        return self.comm_event_counts[CommEvents.message]

    def _record_comm_event(self, broker: str, event: CommEvents, *params: Any):
        self.comm_event_counts[event] += 1
        self.comm_events.append(
            CommEvent(
                datetime.datetime.now(), broker=broker, event=event, params=list(params)
            )
        )

    async def process_message(self, message: Message):
        self._record_comm_event(
            message.header.src,
            CommEvents.message,
            message.header.message_type,
            message.payload,
        )
        self.num_received_by_type[message.header.message_type] += 1
        await super().process_message(message)

    async def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        self._record_comm_event(
            message.payload.client_name,
            CommEvents.mqtt_message,
            message.payload.userdata,
            message.payload.message
        )
        self.num_received_by_topic[message.payload.message.topic] += 1
        await super()._process_mqtt_message(message)

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        self._record_comm_event(
            message.payload.client_name,
            CommEvents.connect,
            message.payload.userdata,
            message.payload.flags,
            message.payload.rc
        )
        super()._process_mqtt_connected(message)

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]):
        self._record_comm_event(
            message.payload.client_name,
            CommEvents.disconnect,
            message.payload.userdata,
            message.payload.rc
        )
        super()._process_mqtt_disconnected(message)

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]):
        self._record_comm_event(
            message.payload.client_name,
            CommEvents.connect_fail,
            message.payload.userdata
        )
        super()._process_mqtt_connect_fail(message)

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        self._record_comm_event(
            message.payload.client_name,
            CommEvents.subscribe,
            message.payload.userdata,
            message.payload.mid, message.payload.granted_qos
        )
        super()._process_mqtt_suback(message)

    def summary_str(self):
        """Summarize results in a string"""
        s = f"Scada2Recorder  {self.node.alias}  num_received: {self.num_received}  comm events: {len(self.comm_events)}"
        if self.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self.num_received_by_topic):
                s += f"\n    {self.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.num_received_by_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self.num_received_by_type):
                s += f"\n    {self.num_received_by_type[message_type]:3d}: [{message_type}]"
        if self.comm_event_counts:
            s += "\n  Comm event counts:"
            for comm_event in self.comm_event_counts:
                s += f"\n    {self.comm_event_counts[comm_event]:3d}: [{comm_event}]"
        if self.comm_events:
            s += "\n  Comm events:"
            for comm_event in self.comm_events:
                s += f"\n    {comm_event}"
        return s
