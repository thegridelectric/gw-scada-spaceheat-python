from collections import defaultdict
from typing import Dict
from typing import List
from typing import Optional

from gwproto import Message
from gwproto.gt.gt_sh_status import GtShStatus_Maker
from gwproto.gt.snapshot_spaceheat import SnapshotSpaceheat_Maker
from gwproto.messages import CommEvent

from actors.utils import gw_mqtt_topic_encode
from actors2 import Scada2
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from proactor.message import MQTTConnectFailPayload
from proactor.message import MQTTConnectPayload
from proactor.message import MQTTDisconnectPayload
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload


class Scada2Recorder(Scada2):

    suppress_status: bool
    num_received_by_topic: Dict[str, int]
    num_received_by_type: Dict[str, int]
    comm_events: List[CommEvent]
    comm_event_counts: Dict[str, int]

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
        return self.comm_event_counts[Message.type_name()]

    # def _record_comm_event(self, broker: str, event: CommEvents, *params: Any):
    #     self.comm_event_counts[event] += 1
    #     self.comm_events.append(
    #         CommEvent(
    #             datetime.datetime.now(), broker=broker, event=event, params=list(params)
    #         )
    #     )

    async def process_message(self, message: Message):
        # self._record_comm_event(
        #     message.Header.Src,
        #     CommEvents.message,
        #     message.Header.MessageType,
        #     message.Payload,
        # )
        self.num_received_by_type[message.Header.MessageType] += 1
        await super().process_message(message)

    def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        # self._record_comm_event(
        #     message.Payload.client_name,
        #     CommEvents.mqtt_message,
        #     message.Payload.userdata,
        #     message.Payload.message
        # )
        self.num_received_by_topic[message.Payload.message.topic] += 1
        super()._process_mqtt_message(message)

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        # self._record_comm_event(
        #     message.Payload.client_name,
        #     CommEvents.connect,
        #     message.Payload.userdata,
        #     message.Payload.flags,
        #     message.Payload.rc
        # )
        super()._process_mqtt_connected(message)

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]):
        # self._record_comm_event(
        #     message.Payload.client_name,
        #     CommEvents.disconnect,
        #     message.Payload.userdata,
        #     message.Payload.rc
        # )
        super()._process_mqtt_disconnected(message)

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]):
        # self._record_comm_event(
        #     message.Payload.client_name,
        #     CommEvents.connect_fail,
        #     message.Payload.userdata
        # )
        super()._process_mqtt_connect_fail(message)

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        # self._record_comm_event(
        #     message.Payload.client_name,
        #     CommEvents.subscribe,
        #     message.Payload.userdata,
        #     message.Payload.mid, message.Payload.granted_qos
        # )
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
