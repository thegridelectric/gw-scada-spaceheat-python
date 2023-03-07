from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Sequence

from gwproto import Message

from gwproactor.message import MQTTReceiptPayload


@dataclass
class LinkStats:
    name: str
    num_received_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    num_received_by_topic: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    comm_event_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    timeouts: int = 0

    @property
    def num_received(self) -> int:
        return self.num_received_by_type[Message.type_name()]

    def __str__(self) -> str:
        s = f"LinkStats [{self.name}]  num_received: {self.num_received}  timeouts: {self.timeouts}"
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
        return s


class ProactorStats:
    num_received_by_type: dict[str, int]
    num_received_by_topic: dict[str, int]
    links: dict[str, LinkStats]

    def __init__(self, link_names: Optional[Sequence[str]] = None):
        self.num_received_by_type = defaultdict(int)
        self.num_received_by_topic = defaultdict(int)
        if link_names is None:
            link_names = []
        self.links = {}
        for link_name in link_names:
            self.add_link(link_name)

    def add_message(self, message: Message) -> None:
        self.num_received_by_type[message.Header.MessageType] += 1

    def add_mqtt_message(self, message: Message[MQTTReceiptPayload]) -> None:
        self.num_received_by_topic[message.Payload.message.topic] += 1
        link_stats = self.link(message.Payload.client_name)
        link_stats.num_received_by_type[Message.type_name()] += 1
        link_stats.num_received_by_type[message.Header.MessageType] += 1
        link_stats.num_received_by_topic[message.Payload.message.topic] += 1

    def total_received(self, message_type: str) -> int:
        return self.num_received_by_type.get(message_type, 0)

    @property
    def num_received(self) -> int:
        return self.num_received_by_type[Message.type_name()]

    @classmethod
    def make_link(cls, link_name: str) -> LinkStats:
        return LinkStats(link_name)

    def add_link(self, link_name: str) -> None:
        if link_name in self.links:
            raise ValueError(f"ERROR. link name {link_name} already present in self.links: {self.links.keys()}")
        self.links[link_name] = self.make_link(link_name)

    def link(self, name: str) -> LinkStats:
        return self.links[name]

    def __str__(self) -> str:
        s = "ProactorStats Stats\n"
        if self.num_received_by_type:
            s += "\nGlobal received by message_type:"
            for message_type in sorted(self.num_received_by_type):
                s += f"\n    {self.num_received_by_type[message_type]:3d}: [{message_type}]"
        for link_name in sorted(self.links):
            s += "\n"
            s += str(self.links[link_name])
        return s
