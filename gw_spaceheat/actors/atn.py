"""Scada implementation"""
import asyncio
import threading
import time
import uuid
from dataclasses import dataclass
from functools import cached_property
from typing import Any
from typing import cast
from typing import Optional
from typing import List
from datetime import datetime
import pytz


from gwproactor.links.link_settings import LinkSettings

from gwproto.named_types import SendSnap
from paho.mqtt.client import MQTTMessageInfo
import rich
from pydantic import BaseModel

from gwproto import create_message_model
from gwproto import MQTTCodec
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.data_channel import DataChannel
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName
from gwproto.messages import ReportEvent
from gwproto.messages import EventBase
from gwproto.messages import PowerWatts
from gwproto.messages import Report
from gwproto.messages import SnapshotSpaceheat
from gwproto.named_types import AnalogDispatch 

from gwproactor import ActorInterface
from gwproactor import QOS
from gwproactor.message import DBGCommands
from gwproactor.message import DBGPayload
from gwproactor.config import LoggerLevels
from gwproactor.message import MQTTReceiptPayload, Message
from gwproactor.proactor_implementation import Proactor

from tests.atn.atn_config import DashboardSettings
from tests.atn.dashboard.dashboard import Dashboard
from tests.atn import messages
from tests.atn.atn_config import AtnSettings

from data_classes.house_0_names import H0N
from named_types import (DispatchContractCounterpartyRequest, Ha1Params, LayoutLite, 
                        ScadaParams, SendLayout)


class AtnMQTTCodec(MQTTCodec):
    exp_src: str
    exp_dst: str = H0N.atn

    def __init__(self, hardware_layout: HardwareLayout):
        self.exp_src = hardware_layout.scada_g_node_alias
        super().__init__(
            create_message_model(
                model_name="AtnMessageDecoder",
                module_names=["named_types","gwproto.messages", "gwproactor.message", "actors.message", ],
                modules=[messages],
            )
        )

    def validate_source_and_destination(self, src: str, dst: str) -> None:
        if src != self.exp_src or dst != self.exp_dst:
            raise ValueError(
                "ERROR validating src and/or dst\n"
                f"  exp: {self.exp_src} -> {self.exp_dst}\n"
                f"  got: {src} -> {dst}"
            )


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
    dashboard: Optional[Dashboard]
    ha1_params: Optional[Ha1Params]

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self._web_manager.disable()
        self.data = AtnData(hardware_layout)
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=Atn.SCADA_MQTT,
                gnode_name=self.hardware_layout.scada_g_node_alias,
                spaceheat_name=H0N.primary_scada,
                mqtt=settings.scada_mqtt,
                codec=AtnMQTTCodec(self.layout),
                downstream=True,
            )
        )
        self.ha1_params = None
        self.latest_report: Optional[Report] = None
        self.report_output_dir = self.settings.paths.data_dir / "report"
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        if self.settings.dashboard.print_gui:
            self.dashboard = Dashboard(
                settings=self.settings.dashboard,
                atn_g_node_alias=self.layout.atn_g_node_alias,
                data_channels=self.layout.data_channels,
                thermostat_names=DashboardSettings.thermostat_names(
                    [channel.Name for channel in self.layout.data_channels.values()]
                ),
                logger=self.logger,
            )
        else:
            self.dashboard = None

    @property
    def name(self) -> str:
        return self._name

    @cached_property
    def short_name(self) -> str:
        return self.layout.atn_g_node_alias.split(".")[-1]

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def publication_name(self) -> str:
        return self.layout.atn_g_node_alias

    @property
    def subscription_name(self) -> str:
        return H0N.atn

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
            case AnalogDispatch():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.Payload)
            case DispatchContractCounterpartyRequest():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload)
            case ScadaParams():
                path_dbg |= 0x00000004
                self._publish_to_scada(message.Payload)
            case SendLayout():
                path_dbg |= 0x00000008
                self._publish_to_scada(message.Payload)
            case SendSnap():
                path_dbg |= 0x00000010
                self._publish_to_scada(message.Payload)
            case DBGPayload():
                path_dbg |= 0x00000020
                self._publish_to_scada(message.Payload)
            case _:
                path_dbg |= 0x00000040

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
            case LayoutLite():
                path_dbg |= 0x00000001
                self._process_layout_lite(decoded.Payload)
            case PowerWatts():
                path_dbg |= 0x00000002
                self._process_pwr(decoded.Payload)
            case Report():
                path_dbg |= 0x00000004
                self._process_report(decoded.Payload)
            case ScadaParams():
                path_dbg |= 0x00000008
                self._process_scada_params(decoded.Payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000010
                self._process_snapshot(decoded.Payload)
            case EventBase():
                path_dbg |= 0x00000020
                self._process_event(decoded.Payload)
                if decoded.Payload.TypeName == ReportEvent.model_fields["TypeName"].default:
                    path_dbg |= 0x00000040
                    self._process_report(decoded.Payload.Report)
                elif decoded.Payload.TypeName == SnapshotSpaceheat.model_fields["TypeName"].default:
                    path_dbg |= 0x00000080
                    self._process_snapshot(decoded.Payload)
            case _:
                path_dbg |= 0x00000100
        self._logger.path("--Atn._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _process_pwr(self, pwr: PowerWatts) -> None:
        if self.settings.dashboard.print_gui:
            self.dashboard.process_power(pwr)
        else:
            rich.print("Received PowerWatts")
            rich.print(pwr)

    def snapshot_str(self, snapshot: SnapshotSpaceheat) -> str:
        s = "\n\nSnapshot received:\n"
        for single_reading in snapshot.LatestReadingList:
            channel = self.layout.data_channels[single_reading.ChannelName]
            telemetry_name = channel.TelemetryName
            if (telemetry_name == TelemetryName.WaterTempCTimes1000
                    or telemetry_name == TelemetryName.WaterTempCTimes1000.value
            ):
                centigrade = single_reading.Value / 1000
                if self.settings.c_to_f:
                    fahrenheit = (centigrade * 9 / 5) + 32
                    extra = f"{fahrenheit:5.2f} F"
                else:
                    extra = f"{centigrade:5.2f} C"
            else:
                extra = (
                    f"{single_reading.Value} "
                    f"{telemetry_name}"
                )
            s += f"  {channel.AboutNodeName}: {extra}\n"
        return s

    def _process_scada_params(self, params: ScadaParams) -> None:
        if params.NewParams:
            print(f"Old: {self.ha1_params}")
            print(f"New: {params.NewParams}")
            self.ha1_params = params.NewParams
        
    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.latest_snapshot = snapshot
        if self.settings.dashboard.print_gui:
            self.dashboard.process_snapshot(snapshot)
        if self.settings.dashboard.print_snap:
            self._logger.warning(self.snapshot_str(snapshot))

    def _process_layout_lite(self, layout: LayoutLite) -> None:
        self.ha1_params = layout.Ha1Params
        self.logger.error(f"Just got layout: {self.ha1_params}")

    def _process_report(self, report: Report) -> None:
        self.data.latest_report = report
        if self.settings.save_events:
            report_file = self.report_output_dir / f"Report.{report.SlotStartUnixS}.json"
            with report_file.open("w") as f:
                f.write(str(report))

    def _process_event(self, event: EventBase) -> None:
        if self.settings.save_events:
            timezone = pytz.timezone("America/New_York")
            event_dt = datetime.fromtimestamp(event.TimeCreatedMs / 1000, tz=timezone)
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
                Payload=SendSnap(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                ),
            )
        )

    def send_new_params(self, new: Ha1Params) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=ScadaParams(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromName=H0N.atn,
                    ToName=H0N.home_alone,
                    UnixTimeMs=int(time.time() * 1000),
                    MessageId=str(uuid.uuid4()),
                    NewParams=new
                ),
            )
        )

    def send_layout(self) -> None:
        self.send_threadsafe(
                        Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=SendLayout(
                            FromGNodeAlias=self.layout.atn_g_node_alias,
                            FromName=H0N.atn,
                            ToName=H0N.primary_scada,
                        ),
                    )
        )
        self.logger.error("Requesting layout")

    def take_control(self) -> float:
        """
        Will trigger Atn mode in scada, if the Scada gets this message
        and is in HomeAlone
        """
        self.send_threadsafe(
            Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=DispatchContractCounterpartyRequest(
                            FromGNodeAlias=self.layout.atn_g_node_alias,
                            BlockchainSig="bogus_algo_sig"
                        ),
                    )
        )

    def set_alpha(self, alpha: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "AlphaTimes10": int(alpha * 10)})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set alpha! {e}")

    def set_beta(self, beta: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "BetaTimes100": int(beta * 100)})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set beta! {e}")
    
    def set_gamma(self, gamma: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "GammaEx6": int(gamma * 1e6)})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set gamma! {e}")

    def set_intermediate_power(self, intermediate_power: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "IntermediatePowerKw": intermediate_power})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set intermediate power! {e}")

    def set_intermediate_rswt(self, intermediate_rswt: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "IntermediateRswtF": int(intermediate_rswt)})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set intermediate rswt! {e}")


    def set_dd_power(self, dd_power: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "DdPowerKw": dd_power})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdPowerKw! {e}")

    def set_dd_rswt(self, dd_rswt: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "DdRswtF": dd_rswt})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdRswt! {e}")

    def set_dd_delta_t(self, dd_delta_t: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate({**self.ha1_params.model_dump(), "DdDeltaTF": dd_delta_t})
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdDeltaTF! {e}")

    def set_dist_010(self, val: int = 30) -> None:
        # TODO: remove lie about this being from auto
        self.send_threadsafe(
             Message(
                Src=self.name,
                Dst=self.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.dist-010v",
                    AboutName="dist-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                ) 
            )
        )

    def set_primary_010(self, val: int = 50) -> None:
        self.send_threadsafe(
             Message(
                Src=self.name,
                Dst=self.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.primary-010v",
                    AboutName="primary-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                ) 
            )
        )

    def set_store_010(self, val: int = 30) -> None:
        self.send_threadsafe(
             Message(
                Src=self.name,
                Dst=self.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.store-010v",
                    AboutName="store-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                )
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

    def _start_derived_tasks(self):
        self._tasks.append(
            asyncio.create_task(self.main(), name="atn-main")
        )

    async def main(self):
        while not self._stop_requested:
            asyncio.sleep(10)

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
