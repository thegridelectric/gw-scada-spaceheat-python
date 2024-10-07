"""Scada implementation"""
import asyncio
import threading
from dataclasses import dataclass
from typing import Any
from typing import cast
from typing import Optional
from typing import List

import pendulum
from gwproto.types import GtShCliAtnCmd
from paho.mqtt.client import MQTTMessageInfo
import rich
from pydantic import BaseModel

from gwproto import create_message_model
from gwproto import MQTTCodec
from gwproto import MQTTTopic
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.data_channel import DataChannel
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName
from gwproto.messages import ReportEvent
from gwproto.messages import SnapshotSpaceheatEvent
from gwproto.messages import EventBase
from gwproto.messages import PowerWatts
from gwproto.messages import Report
from gwproto.messages import SnapshotSpaceheat

from gwproactor import ActorInterface
from gwproactor import QOS
from gwproactor.message import DBGCommands
from gwproactor.message import DBGPayload
from gwproactor.config import LoggerLevels
from gwproactor.message import MQTTReceiptPayload, Message
from gwproactor.proactor_implementation import Proactor


from tests.atn import messages
from tests.atn.atn_config import AtnSettings

class AtnMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            create_message_model(
                model_name="AtnMessageDecoder",
                module_names=["gwproto.messages", "gwproactor.message", "actors.message", ],
                modules=[messages],
            )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.scada_g_node_alias:
            raise Exception(f"alias {source_alias} not my Scada!")

class Telemetry(BaseModel):
    Value: int
    Unit: TelemetryName

@dataclass
class AtnData:
    layout: HardwareLayout
    my_channels: List[DataChannel]
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_report: Optional[Report] = None

    def __init__(self, layout: HardwareLayout):
        self.layout=layout
        self.my_channels = list(layout.data_channels.values())
        self.latest_snapshot = None
        self.latest_report = None

class Atn(ActorInterface, Proactor):
    SCADA_MQTT = "scada"
    data: AtnData
    event_loop_thread: Optional[threading.Thread] = None

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self._web_manager.disable()


        self.data = AtnData(hardware_layout)
        self._links.add_mqtt_link(Atn.SCADA_MQTT, self.settings.scada_mqtt, AtnMQTTCodec(self.layout), primary_peer=True)
        self._links.subscribe(
            Atn.SCADA_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), self.layout.scada_g_node_alias),
            QOS.AtMostOnce,
        )

        self.latest_report: Optional[Report] = None
        self.report_output_dir = self.settings.paths.data_dir / "report"
        self.report_output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
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
            case GtShCliAtnCmd():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.Payload)
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
            case Report():
                path_dbg |= 0x00000004
                self.process_report(decoded.Payload)
            case EventBase():
                path_dbg |= 0x00000008
                self._process_event(decoded.Payload)
                if decoded.Payload.TypeName == ReportEvent.model_fields["TypeName"].default:
                    path_dbg |= 0x00000010
                    self.process_report(decoded.Payload.Report)
                elif decoded.Payload.TypeName == SnapshotSpaceheatEvent.model_fields["TypeName"].default:
                    path_dbg |= 0x00000020
                    self._process_snapshot(decoded.Payload.Snap)
            case _:
                path_dbg |= 0x00000040
        self._logger.path("--Atn._derived_process_mqtt_message  path:0x%08X", path_dbg)

    # noinspection PyMethodMayBeStatic
    def _process_pwr(self, pwr: PowerWatts) -> None:
        rich.print("Received PowerWatts")
        rich.print(pwr)

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.latest_snapshot = snapshot


        if self.settings.print_snap:
            s = "\n\nSnapshot received:\n"
            for single_reading in snapshot.LatestReadingList:
                channel = self.layout.data_channels[single_reading.ChannelName]
                telemetry_name = channel.TelemetryName
                if (telemetry_name == TelemetryName.WaterTempCTimes1000
                   or telemetry_name == TelemetryName.WaterTempCTimes1000.value
                        ):
                    centigrade = single_reading.Value / 1000
                    if self.settings.c_to_f:
                        fahrenheit = (centigrade * 9/5) + 32
                        extra = f"{fahrenheit:5.2f} F"
                    else:
                        extra = f"{centigrade:5.2f} C"
                else:
                    extra = (
                        f"{single_reading.Value} "
                        f"{telemetry_name}"
                    )
                s += f"  {channel.AboutNodeName}: {extra}\n"

            self._logger.warning(s)

            # rich.print(snapshot)

    def process_report(self, report: Report) -> None:
        self.data.latest_report = report
        if self.settings.save_events:
            report_file = self.report_output_dir / f"Report.{report.SlotStartUnixS}.json"
            with report_file.open("w") as f:
                f.write(str(report))


    def _process_event(self, event: EventBase) -> None:
        if self.settings.save_events:
            event_dt = pendulum.from_timestamp(event.TimeNS / 1000000000)
            event_file = (
                self.settings.paths.event_dir
                / f"{event_dt.isoformat()}.{event.TypeName}.uid[{event.MessageId}].json"
            )
            with event_file.open("w") as f:
                f.write(event.model_dump_json(indent=2))

    def snap(self):
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtShCliAtnCmd(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromGNodeId=self.layout.atn_g_node_id,
                    SendSnapshot=True,
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
            f"Atn [{self.node.Name}] total: {self._stats.num_received}  "
            f"report:{self._stats.total_received(Report.model_fields['TypeName'].default)}  "
            f"snapshot:{self._stats.total_received(SnapshotSpaceheat.model_fields['TypeName'].default)}"
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
