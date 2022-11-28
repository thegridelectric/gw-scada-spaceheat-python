from collections import defaultdict
from typing import Dict
from typing import Optional

from actors.atn import Atn
from actors.utils import gw_mqtt_topic_decode
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto.messages import  GtShStatus
from gwproto.messages import  SnapshotSpaceheat
from schema.schema_switcher import TypeMakerByAliasDict


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
            topic = self.decoders.decode_str(type_alias, message.Payload).Header.MessageType
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
