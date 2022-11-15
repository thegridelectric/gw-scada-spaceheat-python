from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import Sequence

from gwproto import Message
from gwproto.messages import CommEvent
from gwproto.messages import EventT

from actors2 import Scada2
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload


@dataclass
class LinkStats:
    name: str
    num_received_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    num_received_by_topic: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    comm_events: list[CommEvent] = field(default_factory=list)
    comm_event_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def num_received(self) -> int:
        return self.comm_event_counts[Message.type_name()]

    def __str__(self) -> str:
        s = f"LinkStats [{self.name}]  num_received: {self.num_received}  comm events: {len(self.comm_events)}"
        if self.num_received_by_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self.num_received_by_type):
                s += f"\n    {self.num_received_by_type[message_type]:3d}: [{message_type}]"
        if self.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self.num_received_by_topic):
                s += f"\n    {self.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.comm_event_counts:
            s += "\n  Comm event counts:"
            for comm_event in self.comm_event_counts:
                s += f"\n    {self.comm_event_counts[comm_event]:3d}: [{comm_event}]"
        if self.comm_events:
            s += "\n  Comm events:"
            for comm_event in self.comm_events:
                s += f"\n    {comm_event}"
        return s


class Stats:
    num_received_by_type: dict[str, int]
    links: dict[str, LinkStats]

    def __init__(self, link_names: Optional[Sequence[str]] = None):
        self.num_received_by_type = defaultdict(int)
        if link_names is None:
            link_names = []
        self.links = {link_name: LinkStats(link_name) for link_name in link_names}

    def link(self, name: str):
        return self.links[name]

    def __str__(self) -> str:
        s = "ScadaRecorder2 Stats\n"
        if self.num_received_by_type:
            s += "\nGlobal received by message_type:"
            for message_type in sorted(self.num_received_by_type):
                s += f"\n    {self.num_received_by_type[message_type]:3d}: [{message_type}]"
        for link_name in sorted(self.links):
            s += "\n"
            s += str(self.links[link_name])
        return s

class Scada2Recorder(Scada2):

    suppress_status: bool
    stats: Stats
    subacks_paused: bool
    pending_subacks: list[Message]

    def __init__(self, name: str, settings: ScadaSettings, hardware_layout: HardwareLayout, actor_nodes: Optional[List[ShNode]] = None):
        self.suppress_status = False
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout, actor_nodes=actor_nodes)
        # noinspection PyProtectedMember
        self.stats = Stats(self._mqtt_clients._clients)
        self.subacks_paused = False
        self.pending_subacks = []

    def time_to_send_status(self) -> bool:
        return not self.suppress_status and super().time_to_send_status()

    def generate_event(self, event: EventT) -> None:
        if isinstance(event, CommEvent):
            link_stats = self.stats.links[event.PeerName]
            link_stats.comm_event_counts[event.TypeName] += 1
            link_stats.comm_events.append(event)
        super().generate_event(event)

    def pause_subacks(self):
        self.subacks_paused = True

    def release_subacks(self):
        self.subacks_paused = False
        for message in self.pending_subacks:
            self._receive_queue.put_nowait(message)

    async def process_message(self, message: Message):
        if self.subacks_paused and isinstance(message.Payload, MQTTSubackPayload):
            self.pending_subacks.append(message)
        else:
            self.stats.num_received_by_type[message.Header.MessageType] += 1
            if isinstance(message.Payload, MQTTReceiptPayload):
                self.stats.links[message.Payload.client_name].num_received_by_type[message.Header.MessageType] += 1
            await super().process_message(message)

    def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        self.stats.links[message.Payload.client_name].num_received_by_topic[message.Payload.message.topic] += 1
        super()._process_mqtt_message(message)

    def summary_str(self):
        return str(self.stats)
