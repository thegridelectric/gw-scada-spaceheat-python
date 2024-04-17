"""Scada implementation"""
import asyncio
import dataclasses
import threading
import time
from dataclasses import dataclass
from typing import Any
from typing import cast
from typing import Optional
from typing import Sequence

import pendulum
from paho.mqtt.client import MQTTMessageInfo
import rich
from pydantic import BaseModel

from gwproto import CallableDecoder
from gwproto import Decoders
from gwproto import create_message_payload_discriminator
from gwproto import MQTTCodec
from gwproto import MQTTTopic
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName
from gwproto.messages import GtShStatusEvent
from gwproto.messages import SnapshotSpaceheatEvent
from gwproto.messages import EventBase
from gwproto.messages import PowerWatts
from gwproto.messages import PowerWatts_Maker
from gwproto.messages import GtDispatchBoolean_Maker
from gwproto.messages import GtShCliAtnCmd_Maker
from gwproto.messages import GtShStatus
from gwproto.messages import SnapshotSpaceheat
from gwproto.messages import GsPwr_Maker
from gwproto.messages import GtShStatus_Maker
from gwproto.messages import SnapshotSpaceheat_Maker

from gwproactor import ActorInterface
from gwproactor import QOS
from gwproactor.message import DBGCommands
from gwproactor.message import DBGPayload
from gwproactor.config import LoggerLevels
from gwproactor.message import MQTTReceiptPayload, Message
from gwproactor.proactor_implementation import Proactor

from enums import Role
from actors import message as actor_message # noqa

from tests.atn import messages
from tests.atn.atn_config import AtnSettings

AtnMessageDecoder = create_message_payload_discriminator(
    model_name="AtnMessageDecoder",
    module_names=["gwproto.messages", "gwproactor.message", "actors.message", ],
    modules=[messages],
)


class AtnMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            Decoders.from_objects(
                [
                    GtShStatus_Maker,
                    SnapshotSpaceheat_Maker,
                    PowerWatts_Maker,
                ],
                message_payload_discriminator=AtnMessageDecoder,
            ).add_decoder("p", CallableDecoder(lambda decoded: GsPwr_Maker(decoded[0]).tuple))
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.scada_g_node_alias:
            raise Exception(f"alias {source_alias} not my Scada!")

class Telemetry(BaseModel):
    Value: int
    Unit: TelemetryName

class RecentRelayState(BaseModel):
    State: Optional[int] = None
    LastChangeTimeUnixMs: Optional[int] = None

@dataclass
class AtnData:
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_status: Optional[GtShStatus] = None
    relay_state: dict[ShNode, RecentRelayState] = dataclasses.field(default_factory=dict)

class Atn(ActorInterface, Proactor):
    SCADA_MQTT = "scada"

    data: AtnData
    my_sensors: Sequence[ShNode]
    my_relays: Sequence[ShNode]
    event_loop_thread: Optional[threading.Thread] = None

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self.my_sensors = list(
            filter(
                lambda x: (
                    x.role == Role.TankWaterTempSensor
                    or x.role == Role.BooleanActuator
                    or x.role == Role.PipeTempSensor
                    or x.role == Role.PipeFlowMeter
                    or x.role == Role.PowerMeter
                ),
                list(self.layout.nodes.values()),
            )
        )
        self.my_relays = list(
            filter(lambda x: x.role == Role.BooleanActuator, list(self.layout.nodes.values()))
        )
        self.data = AtnData(relay_state={x: RecentRelayState() for x in self.my_relays})
        self._links.add_mqtt_link(Atn.SCADA_MQTT, self.settings.scada_mqtt, AtnMQTTCodec(self.layout), primary_peer=True)
        self._links.subscribe(
            Atn.SCADA_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), self.layout.scada_g_node_alias),
            QOS.AtMostOnce,
        )

        self.latest_status: Optional[GtShStatus] = None
        self.status_output_dir = self.settings.paths.data_dir / "status"
        self.status_output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def alias(self) -> str:
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def publication_name(self) -> str:
        return self.layout.atn_g_node_alias

    @property
    def settings(self) -> AtnSettings:
        return cast(AtnSettings, self._settings)

    @property
    def layout(self) -> HardwareLayout:
        return self._layout

    def init(self):
        """Called after constructor so derived functions can be used in setup."""


    def _publish_to_scada(self, payload, qos: QOS = QOS.AtMostOnce) -> MQTTMessageInfo:
        return self._links.publish_message(
            Atn.SCADA_MQTT,
            Message(Src=self.publication_name, Payload=payload),
            qos=qos
        )

    def _derived_process_message(self, message: Message):
        self._logger.path(
            "++Atn._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType
        )
        path_dbg = 0
        match message.Payload:
            case GtShCliAtnCmd_Maker():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.Payload.tuple.as_dict())
            case GtDispatchBoolean_Maker():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload.tuple.as_dict())
            case DBGPayload():
                path_dbg |= 0x00000004
                self._publish_to_scada(message.Payload)
            case _:
                path_dbg |= 0x00000008

        self._logger.path("--Atn._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(self, message: Message[MQTTReceiptPayload], decoded: Any):
        self._logger.path("++Atn._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name != self.SCADA_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.Payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.Payload.message.topic}]"
            )
        self.stats.add_message(decoded)
        match decoded.Payload:
            case PowerWatts():
                path_dbg |= 0x00000001
                self._process_pwr(decoded.Payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000002
                self._process_snapshot(decoded.Payload)
            case GtShStatus():
                path_dbg |= 0x00000004
                self._process_status(decoded.Payload)
            case EventBase():
                path_dbg |= 0x00000008
                self._process_event(decoded.Payload)
                if decoded.Payload.TypeName == GtShStatusEvent.__fields__["TypeName"].default:
                    path_dbg |= 0x00000010
                    self._process_status(decoded.Payload.status)
                elif decoded.Payload.TypeName == SnapshotSpaceheatEvent.__fields__["TypeName"].default:
                    path_dbg |= 0x00000020
                    self._process_snapshot(decoded.Payload.snap)
            case _:
                path_dbg |= 0x00000040
        self._logger.path("--Atn._derived_process_mqtt_message  path:0x%08X", path_dbg)

    # noinspection PyMethodMayBeStatic
    def _process_pwr(self, pwr: PowerWatts) -> None:
        rich.print("Received PowerWatts")
        rich.print(pwr)

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.latest_snapshot = snapshot
        for node in self.my_relays:
            possible_indices = []
            for idx in range(len(snapshot.Snapshot.AboutNodeAliasList)):
                if (
                    snapshot.Snapshot.AboutNodeAliasList[idx] == node.alias
                    and snapshot.Snapshot.TelemetryNameList[idx] == TelemetryName.RelayState
                ):
                    possible_indices.append(idx)
            if len(possible_indices) != 1:
                continue
            idx = possible_indices[0]
            old_state = self.data.relay_state[node].State
            if old_state != snapshot.Snapshot.ValueList[idx]:
                self.data.relay_state[node].State = snapshot.Snapshot.ValueList[idx]
                self.data.relay_state[node].LastChangeTimeUnixMs = int(time.time() * 1000)

        s = "\n\nSnapshot received:\n"
        for i in range(len(snapshot.Snapshot.AboutNodeAliasList)):
            telemetry_name = snapshot.Snapshot.TelemetryNameList[i]
            if (telemetry_name == TelemetryName.WaterTempCTimes1000
               or telemetry_name == TelemetryName.WaterTempCTimes1000.value
                    ):
                centigrade = snapshot.Snapshot.ValueList[i] / 1000
                if self.settings.c_to_f:
                    fahrenheit = (centigrade * 9/5) + 32
                    extra = f"{fahrenheit:5.2f} F"
                else:
                    extra = f"{centigrade:5.2f} C"
            else:
                extra = (
                    f"{snapshot.Snapshot.ValueList[i]} "
                    f"{snapshot.Snapshot.TelemetryNameList[i].value}"
                )
            s += f"  {snapshot.Snapshot.AboutNodeAliasList[i]}: {extra}\n"
        # s += f"snapshot is None:{snapshot is None}\n"
        # s += "json.dumps(snapshot.asdict()):\n"
        # s += json.dumps(snapshot.asdict(), sort_keys=True, indent=2)
        # s += "\n"
        self._logger.warning(s)

        # rich.print(snapshot)

    def _process_status(self, status: GtShStatus) -> None:
        self.data.latest_status = status
        if self.settings.save_events:
            status_file = self.status_output_dir / f"GtShStatus.{status.SlotStartUnixS}.json"
            with status_file.open("w") as f:
                f.write(status.as_type())
        # self._logger.info(f"Wrote status file [{status_file}]")
        if self.settings.print_status:
            rich.print("Received GtShStatus")
            rich.print(status)

    def _process_event(self, event: EventBase) -> None:
        if self.settings.save_events:
            event_dt = pendulum.from_timestamp(event.TimeNS / 1000000000)
            event_file = (
                self.settings.paths.event_dir
                / f"{event_dt.isoformat()}.{event.TypeName}.uid[{event.MessageId}].json"
            )
            with event_file.open("w") as f:
                f.write(event.json(sort_keys=True, indent=2))

    def snap(self):
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtShCliAtnCmd_Maker(
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_id=self.layout.atn_g_node_id,
                    send_snapshot=True,
                ),
            )
        )

    def dbg(
        self,
        message_summary: int = -1,
        lifecycle: int = -1,
        comm_event: int = -1,
        command: Optional[DBGCommands | str] = None,
    ):
        self.send_dbg_to_peer(
            message_summary=message_summary,
            lifecycle=lifecycle,
            comm_event=comm_event,
            command=command
        )

    def send_dbg_to_peer(
        self,
        message_summary: int = -1,
        lifecycle: int = -1,
        comm_event: int = -1,
        command: Optional[DBGCommands | str] = None,
    ):
        if isinstance(command, str):
            command = DBGCommands(command)
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=DBGPayload(
                    Levels=LoggerLevels(
                        message_summary=message_summary,
                        lifecycle=lifecycle,
                        comm_event=comm_event,
                    ),
                    Command=command,
                ),
            )
        )

    def set_relay(self, name: str, state: bool) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtDispatchBoolean_Maker(
                    about_node_name=name,
                    to_g_node_alias=self.layout.scada_g_node_alias,
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_instance_id=self.layout.atn_g_node_instance_id,
                    relay_state=int(state),
                    send_time_unix_ms=int(time.time() * 1000),
                ),
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
            f"Atn [{self.node.alias}] total: {self._stats.num_received}  "
            f"status:{self._stats.total_received(GtShStatus_Maker.type_name)}  "
            f"snapshot:{self._stats.total_received(SnapshotSpaceheat_Maker.type_name)}"
        )
        if self._stats.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self._stats.num_received_by_topic):
                s += f"\n    {self._stats.num_received_by_topic[topic]:3d}: [{topic}]"
        if self._stats.num_received_by_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self._stats.num_received_by_type):
                s += f"\n    {self._stats.num_received_by_type[message_type]:3d}: [{message_type}]"

        return s

    def latest_simple_reading(self, node: ShNode) -> Optional[Telemetry]:
        """Provides the latest reported Telemetry value as reported in a snapshot
        message from the Scada, for a simple sensor.

        Args:
            node (ShNode): A Spaceheat Node associated to a simple sensor.

        Returns:
            Optional[int]: Returns None if no value has been reported.
            This will happen for example if the node is not associated to
            a simple sensor.
        """
        snap = self.data.latest_snapshot.Snapshot
        try:
            idx = snap.AboutNodeAliasList.index(node.alias)
        except ValueError:
            return None

        return Telemetry(Value=snap.ValueList[idx], Unit=snap.TelemetryNameList[idx])