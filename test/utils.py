import datetime
import enum
import pprint
import socket
import textwrap
import time
from collections import defaultdict
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field

import settings
from actors.atn import Atn
from actors.cloud_ear import CloudEar
from actors.scada import Scada
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch import GsDispatch
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import (
    GtDispatchBooleanLocal,
)
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response import (
    GtShCliScadaResponse,
)

LOCAL_MQTT_MESSAGE_DELTA_S = settings.LOCAL_MQTT_MESSAGE_DELTA_S
GW_MQTT_MESSAGE_DELTA = settings.GW_MQTT_MESSAGE_DELTA


class Brokers(enum.Enum):
    invalid = "invalid"
    gw = "gw"
    local = "local"


class CommEvents(enum.Enum):
    invalid = "invalid"
    connect = "connect"
    connect_fail = "connect_fail"
    subscribe = "subscribe"
    message = "message"
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
    broker: Brokers = Brokers.invalid
    event: CommEvents = CommEvents.invalid
    params: List = field(default_factory=list)

    def __str__(self):
        param_str = str(self.params)
        max_param_width = 80
        if len(param_str) > max_param_width:
            param_str = param_str[:max_param_width] + "..."
        return f"{self.timestamp.isoformat()}  {self.broker.value:5s}  {self.event.value:23s}  {param_str}"

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
            f"ERROR. Function {f} timed out after {timeout} seconds. {tag}"
        )
    else:
        return False


class AtnRecorder(Atn):
    cli_resp_received: int
    latest_cli_response_payload: Optional[GtShCliScadaResponse]

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.cli_resp_received = 0
        self.latest_cli_response_payload: Optional[GtShCliScadaResponse] = None
        super().__init__(node, logging_on=logging_on)

    def on_gw_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShCliScadaResponse):
            self.cli_resp_received += 1
            self.latest_cli_response_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        return (
            f"AtnRecorder [{self.node.alias}] cli_resp_received: {self.cli_resp_received}  "
            f"latest_cli_response_payload: {self.latest_cli_response_payload}"
        )


class EarRecorder(CloudEar):
    num_received: int
    num_received_by_topic: Dict[str, int]
    latest_payload: Optional[Any]

    def __init__(self, logging_on: bool = False):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.latest_payload = None
        super().__init__(logging_on=logging_on)

    def on_gw_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
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

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.num_received_by_topic = defaultdict(int)
        self.comm_events = []
        self.comm_event_counts = defaultdict(int)
        super().__init__(node, logging_on=logging_on)
        self.gw_client.on_subscribe = self.on_gw_subscribe
        self.gw_client.on_publish = self.on_gw_publish
        self.gw_client.on_unsubscribe = self.on_gw_unsubscribe
        self.gw_client.on_socket_open = self.on_gw_socket_open
        self.gw_client.on_socket_close = self.on_gw_socket_close
        # on_socket_register_write AND on_socket_unregister_write callbacks are meant for
        # integration with event loops external to paho. They are also noisy, so we don't
        # use them here.

    @property
    def num_received(self) -> int:
        return self.comm_event_counts[CommEvents.message]

    def _record_comm_event(self, broker: Brokers, event: CommEvents, *params: Any):
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
        self._record_comm_event(Brokers.local, CommEvents.message, userdata, message)
        self.num_received_by_topic[message.topic] += 1
        super().on_mqtt_message(client, userdata, message)

    def on_gw_mqtt_message(self, client, userdata, message):
        self._record_comm_event(Brokers.gw, CommEvents.message, userdata, message)
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_connect(self, client, userdata, flags, rc):
        self._record_comm_event(Brokers.gw, CommEvents.connect, userdata, flags, rc)
        super().on_gw_connect(client, userdata, flags, rc)

    def on_gw_connect_fail(self, client, userdata, rc):
        self._record_comm_event(Brokers.gw, CommEvents.connect_fail, userdata, rc)
        super().on_gw_connect_fail(client, userdata, rc)

    def on_gw_disconnect(self, client, userdata, rc):
        self._record_comm_event(Brokers.gw, CommEvents.disconnect, userdata, rc)
        super().on_gw_disconnect(client, userdata, rc)

    def on_gw_publish(self, _, userdata, mid):
        self._record_comm_event(Brokers.gw, CommEvents.publish, userdata, mid)

    def on_gw_subscribe(self, _, userdata, mid, granted_qos):
        self._record_comm_event(
            Brokers.gw, CommEvents.subscribe, userdata, mid, granted_qos
        )

    def on_gw_unsubscribe(self, _, userdata, mid):
        self._record_comm_event(Brokers.gw, CommEvents.unsubscribe, userdata, mid)

    def on_gw_socket_open(self, _, userdata, sock):
        self._record_comm_event(
            Brokers.gw, CommEvents.socket_open, userdata, self._socket_str(sock)
        )

    def on_gw_socket_close(self, _, userdata, sock):
        self._record_comm_event(
            Brokers.gw, CommEvents.socket_close, userdata, self._socket_str(sock)
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
