"""Scada implementation"""
import asyncio
import logging
import sys
import threading
import time
from collections import defaultdict
from typing import Any
from typing import Optional
from typing import Sequence

import dotenv
from paho.mqtt.client import MQTTMessageInfo

from gwproto import DecoderExtractor
from gwproto import create_message_payload_discriminator
from gwproto.messages import GsPwr
from gwproto.messages import GtDispatchBoolean_Maker
from gwproto.messages import GtShCliAtnCmd_Maker
from gwproto.messages import GtShStatus
from gwproto.messages import SnapshotSpaceheat
from gwproto.messages import GsPwr_Maker
from gwproto.messages import GtShStatus_Maker
from gwproto.messages import SnapshotSpaceheat_Maker

from actors.utils import gw_mqtt_topic_encode
from actors.utils import QOS
from actors2 import ActorInterface
from actors2.scada2 import ScadaMQTTCodec
from command_line_utils import parse_args
from config import LoggingSettings
from config import Paths
from logging_setup import setup_logging
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from proactor.logger import ProactorLogger
from proactor.message import MQTTReceiptPayload, Message
from proactor.proactor_implementation import Proactor
from schema.enums import Role
from tests.atn.atn_config import AtnSettings
from tests.atn  import messages

AtnMessageDecoder = create_message_payload_discriminator(
    model_name="AtnMessageDecoder",
    module_names=[
        "gwproto.messages",
        "actors2.message"
    ],
    modules=[messages]
)


class AtnMQTTCodec(ScadaMQTTCodec):

    def __init__(self, hardware_layout: HardwareLayout):
        super().__init__(
            hardware_layout,
            decoders=DecoderExtractor().from_objects(
                [
                    GtShStatus_Maker,
                    SnapshotSpaceheat_Maker,
                ],
                message_payload_discriminator=AtnMessageDecoder,
            ).add_decoder(
            "p",
            lambda decoded: GsPwr_Maker(decoded[0]).tuple
        )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.scada_g_node_alias:
            raise Exception(f"alias {source_alias} not my Scada!")


class MessageStats:
    num_received: int
    num_received_by_topic: dict[str, int]
    num_received_by_message_type: dict[str, int]

    def __init__(self):
        self.reset()

    def reset(self):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.num_received_by_message_type = defaultdict(int)

    def add_message(self, message: Message) -> None:
        self.num_received += 1
        self.num_received_by_message_type[message.header.message_type] += 1

    def add_mqtt_message(self, message: Message[MQTTReceiptPayload]) -> None:
        self.num_received_by_message_type[message.header.message_type] += 1
        self.num_received_by_topic[message.payload.message.topic] += 1

    @property
    def num_status_received(self) -> int:
        return self.num_received_by_message_type[GtShStatus_Maker.type_alias]

    @property
    def num_snapshot_received(self) -> int:
        return self.num_received_by_message_type[SnapshotSpaceheat_Maker.type_alias]

class AtnData:
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_status: Optional[GtShStatus] = None

class Atn2(ActorInterface, Proactor):
    SCADA_MQTT = "scada"

    settings: AtnSettings
    layout: HardwareLayout
    _node: ShNode
    data: AtnData
    stats: MessageStats
    my_sensors: Sequence[ShNode]
    event_loop_thread: Optional[threading.Thread] = None

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(
            name=name,
            logger=ProactorLogger(**settings.logging.qualified_logger_names())
        )
        self._node = hardware_layout.node(name)
        self.data = AtnData()
        self.settings = settings
        self.layout = hardware_layout
        self.my_sensors = list(
            filter(
                lambda x: (
                        x.role == Role.TANK_WATER_TEMP_SENSOR
                        or x.role == Role.BOOLEAN_ACTUATOR
                        or x.role == Role.PIPE_TEMP_SENSOR
                        or x.role == Role.PIPE_FLOW_METER
                        or x.role == Role.POWER_METER
                ),
                list(self.layout.nodes.values()),
            )
        )
        self._add_mqtt_client(
            Atn2.SCADA_MQTT, self.settings.scada_mqtt, AtnMQTTCodec(self.layout)
        )
        # TODO: take care of subscriptions better. They should be registered here and only subscribed on connect.
        self._mqtt_clients.subscribe(
            Atn2.SCADA_MQTT,
            gw_mqtt_topic_encode(f"{self.layout.scada_g_node_alias}/{Message.__fields__['type_name'].default}"),
            QOS.AtMostOnce,
        )
        self.latest_status: Optional[GtShStatus] = None
        self.status_output_dir = self.settings.paths.data_dir / "status"
        self.status_output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = MessageStats()

    @property
    def alias(self) -> str:
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    def _publish_to_scada(
        self, payload, qos: QOS = QOS.AtMostOnce
    ) -> MQTTMessageInfo:
        message = Message(src=self.layout.atn_g_node_alias, payload=payload)
        return self._encode_and_publish(
            Atn2.SCADA_MQTT,
            topic=gw_mqtt_topic_encode(message.mqtt_topic()),
            payload=message,
            qos=qos,
        )

    async def process_message(self, message: Message):
        self.stats.add_message(message)
        await super().process_message(message)

    async def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        self.stats.add_mqtt_message(message)
        await super()._process_mqtt_message(message)


    async def _derived_process_message(self, message: Message):
        self._logger.path("++Atn2._derived_process_message %s/%s", message.header.src, message.header.message_type)
        path_dbg = 0
        match message.payload:
            case GtShCliAtnCmd_Maker():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.payload.tuple.asdict())
            case GtDispatchBoolean_Maker():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.payload.tuple.asdict())
            case _:
                path_dbg |= 0x00000004

        self._logger.path("--Atn2._derived_process_message  path:0x%08X", path_dbg)

    async def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path("++Atn2._derived_process_mqtt_message %s", message.payload.message.topic)
        path_dbg = 0
        if message.payload.client_name != self.SCADA_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.payload.message.topic}]"
            )
        self.stats.add_message(decoded)
        match decoded.payload:
            case GsPwr():
                path_dbg |= 0x00000001
                self._process_pwr(decoded.payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000002
                self._process_snapshot(decoded.payload)
            case GtShStatus():
                path_dbg |= 0x00000004
                self._process_status(decoded.payload)
            case _:
                path_dbg |= 0x00000008
        self._logger.path("--Atn2._derived_process_mqtt_message  path:0x%08X", path_dbg)


    def _process_pwr(self, pwr: GsPwr) -> None:
        pass

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.latest_snapshot = snapshot
        self._logger.info("Snapshot received:")
        for node in self.my_sensors:
            if node.alias not in snapshot.Snapshot.AboutNodeAliasList:
                self._logger.info("  No data for node %s present in snapshot", node.alias)
        for i in range(len(snapshot.Snapshot.AboutNodeAliasList)):
            self._logger.info(
                "  %s: %s %s",
                snapshot.Snapshot.AboutNodeAliasList[i],
                snapshot.Snapshot.ValueList[i],
                snapshot.Snapshot.TelemetryNameList[i].value
            )

    def _process_status(self, status: GtShStatus) -> None:
        self.data.latest_status = status


    def get_snapshot(self):
        self.send_threadsafe(
            Message(
                src=self.name,
                dst=self.name,
                payload=GtShCliAtnCmd_Maker(
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_id=self.layout.atn_g_node_id,
                    send_snapshot=True,
                )
            )
        )

    def set_relay(self, name: str, state: bool) -> None:
        self.send_threadsafe(
            Message(
                src=self.name,
                dst=self.name,
                payload=GtDispatchBoolean_Maker(
                    about_node_alias=name,
                    to_g_node_alias=self.layout.scada_g_node_alias,
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_id=self.layout.atn_g_node_id,
                    relay_state=int(state),
                    send_time_unix_ms=int(time.time() * 1000),
                )
            )
        )

    def turn_on(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, True)

    def turn_off(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, False)

    def start(self):
        if self.event_loop_thread is not None:
            raise ValueError("ERROR. start() already called once.")
        self.event_loop_thread = threading.Thread(target=asyncio.run, args=[self.run_forever()])
        self.event_loop_thread.start()

    def stop_and_join_thread(self):
        self.stop()
        if self.event_loop_thread is not None and self.event_loop_thread.is_alive():
            self.event_loop_thread.join()

    def summary_str(self) -> str:
        """Summarize results in a string"""
        s = (
            f"Atn [{self.node.alias}] total: {self.stats.num_received}  "
            f"status:{self.stats.num_status_received}  snapshot:{self.stats.num_snapshot_received}"
        )
        if self.stats.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self.stats.num_received_by_topic):
                s += f"\n    {self.stats.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.stats.num_received_by_message_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self.stats.num_received_by_message_type):
                s += f"\n    {self.stats.num_received_by_message_type[message_type]:3d}: [{message_type}]"

        return s

    @classmethod
    def get_atn(cls, argv: Optional[Sequence[str]] = None, start: bool = True) -> "Atn2":
        if argv is None:
            argv = sys.argv[1:]
            if "-v" not in argv and "--verbose" not in argv:
                argv.append("-v")
        args = parse_args(argv)
        env_path = dotenv.find_dotenv(args.env_file)
        dotenv.load_dotenv(env_path)
        settings = AtnSettings(
            paths=Paths(
                name="atn",
                hardware_layout=Paths().hardware_layout
            ),
            logging=LoggingSettings(base_log_name="gridworks.atn")
        )
        settings.paths.mkdirs()
        setup_logging(args, settings)  # type: ignore
        logger = logging.getLogger(settings.logging.base_log_name)
        logger.info(f"Env file: {env_path}")
        layout = HardwareLayout.load(settings.paths.hardware_layout)
        a = Atn2("a", settings, layout)
        if start:
            a.start()
        return a


