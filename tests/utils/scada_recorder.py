import datetime
import pprint
import socket
import textwrap
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List

from actors.scada import Scada
from actors.utils import gw_mqtt_topic_encode
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto.messages import GtDispatchBooleanLocal
from gwproto.messages import GtShStatus_Maker
from gwproto.messages import SnapshotSpaceheat_Maker
from gwproto.messages import GsDispatch

from tests.utils.comm_events import CommEvent
from tests.utils.comm_events import CommEvents


class ScadaRecorder(Scada):
    """Record data about a PrimaryScada execution during test"""

    num_received_by_topic: Dict[str, int]
    num_received_by_type: Dict[str, int]
    comm_events: List[CommEvent]
    comm_event_counts: Dict[CommEvents, int]

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.num_received_by_topic = defaultdict(int)
        self.num_received_by_type = defaultdict(int)
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
        self.num_received_by_type[message.topic.split("/")[-1]] += 1
        super().on_mqtt_message(client, userdata, message)

    def on_gw_mqtt_message(self, client, userdata, message):
        self._record_comm_event("gridworks", CommEvents.message, userdata, message)
        self.num_received_by_topic[message.topic] += 1
        self.num_received_by_type[message.topic.split("/")[-1]] += 1
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
            s += f"\n    {self.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.num_received_by_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self.num_received_by_type):
                s += f"\n    {self.num_received_by_type[message_type]:3d}: [{message_type}]"
        if self.comm_event_counts:
            s += f"\n{textwrap.indent(pprint.pformat(self.comm_event_counts), '  ')}"
        if self.comm_events:
            s += "\n  Comm events:"
            for comm_event in self.comm_events:
                s += f"\n    {comm_event}"
        return s
