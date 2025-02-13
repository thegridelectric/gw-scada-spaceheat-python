"""Scada implementation"""
import csv
import asyncio
import json
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np
import pytz
import aiohttp
import rich
from actors.flo import DGraph
from data_classes.house_0_layout import House0Layout
from data_classes.house_0_names import H0CN, H0N
from enums import MarketPriceUnit, MarketQuantityUnit, MarketTypeName
from named_types import RemainingElecEvent, GameOn
from named_types import HackOilOn, HackOilOff
from data_classes.house_0_names import House0RelayIdx

from gwproactor import QOS, ActorInterface
from gwproactor.config import LoggerLevels
from gwproactor.links.link_settings import LinkSettings
from gwproactor.message import DBGCommands, DBGPayload, MQTTReceiptPayload
from gwproactor.proactor_implementation import Proactor
from gwproto import Message, MQTTCodec, create_message_model
from gwproto.data_classes.data_channel import DataChannel
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName, RelayClosedOrOpen
from gwproto.messages import (EventBase, PowerWatts, Report, ReportEvent)
from gwproto.named_types import AnalogDispatch, SendSnap, MachineStates
from named_types import (AtnBid, DispatchContractGoDormant,
                         DispatchContractGoLive, EnergyInstruction, FloParamsHouse0,
                         Ha1Params, LatestPrice, LayoutLite, PriceQuantityUnitless, 
                         ScadaParams, SendLayout, SnapshotSpaceheat)

from paho.mqtt.client import MQTTMessageInfo
from pydantic import BaseModel
from transitions import Machine

from tests.atn import messages
from tests.atn.atn_config import AtnSettings, DashboardSettings
from tests.atn.dashboard.dashboard import Dashboard


class AtnMQTTCodec(MQTTCodec):
    exp_src: str
    exp_dst: str = H0N.atn

    def __init__(self, hardware_layout: House0Layout):
        self.exp_src = hardware_layout.scada_g_node_alias
        super().__init__(
            create_message_model(
                model_name="AtnMessageDecoder",
                module_names=[
                    "named_types",
                    "gwproto.messages",
                    "gwproactor.message",
                    "actors.message",
                ],
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
    layout: House0Layout
    my_channels: List[DataChannel]
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_report: Optional[Report] = None

    def __init__(self, layout: House0Layout):
        self.layout = layout
        self.my_channels = list(layout.data_channels.values())
        self.latest_snapshot = None
        self.latest_report = None


class Atn(ActorInterface, Proactor):
    MAIN_LOOP_SLEEP_SECONDS = 61
    P_NODE = "hw1.isone.ver.keene"
    SCADA_MQTT = "scada"
    data: AtnData
    event_loop_thread: Optional[threading.Thread] = None
    dashboard: Optional[Dashboard]
    ha1_params: Optional[Ha1Params]

    states = [
        "DispatchDormantScadaReady",
        "DispatchDormantScadaNotReady",
        "DispatchLive"
    ]

    transitions = [
        {"trigger": "ScadaReadyReceived", "source": "DispatchDormantScadaNotReady", "dest": "DispatchDormantScadaReady"},
        {"trigger": "AtnWantsControl", "source": "DispatchDormantScadaReady", "dest": "DispatchLive"},
        {"trigger": "AtnReleasesControl", "source": "DispatchLive", "dest": "DispatchDormantScadaNotReady"},
        {"trigger": "ScadaLinkDead", "source": "DispatchLive", "dest": "DispatchDormantScadaNotReady"},
         {"trigger": "ScadaLinkDead", "source": "DispatchDormantScadaReady", "dest": "DispatchDormantScadaNotReady"}

    ]

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: House0Layout,
    ):
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self.latest_remaining_elec = None
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
        self.machine = Machine(
            model=self,
            states=Atn.states,
            transitions=Atn.transitions,
            initial="DispatchDormantScadaNotReady",
            send_event=False,
        ) 
        self.log(f"State is {self.state}")
        self.is_simulated = self.settings.is_simulated
        self.latest_channel_values: Dict[str, int] = {}
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.latitude = self.settings.latitude
        self.longitude = self.settings.longitude
        self.sent_bid = False
        self.latest_bid = None
        self.hp_is_off = False
        self.weather_forecast = None
        self.coldest_oat_by_month = [-3, -7, 1, 21, 30, 31, 46, 47, 28, 24, 16, 0]
        self.price_forecast = None
        self.data_channels: List
        self.temperature_channel_names = None
        self.ha1_params: Optional[Ha1Params] = None
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

        self.latest_price: Optional[LatestPrice] = None

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
    def scada(self) -> ShNode:
        return self.layout.node(H0N.primary_scada)

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
    def layout(self) -> House0Layout:
        return cast(House0Layout, self._layout)

    def init(self):
        """Called after constructor so derived functions can be used in setup."""

    def _publish_to_scada(self, payload, qos: QOS = QOS.AtMostOnce) -> MQTTMessageInfo:
        return self._links.publish_message(
            Atn.SCADA_MQTT, Message(Src=self.publication_name, Payload=payload), qos=qos
        )

    def _derived_process_message(self, message: Message):
        self._logger.path(
            "++Atn._derived_process_message %s/%s",
            message.Header.Src,
            message.Header.MessageType,
        )
        if message.Header.Dst == self.scada.name:
            self._publish_to_scada(message.Payload)
        else:
            self.process_atn_message(message)
    
    def process_atn_message(self, message: Message):
        path_dbg = 0
        match message.Payload:
            case LatestPrice():
                path_dbg |= 0x00000100
                self.latest_price_received(message.Payload)
            case _:
                path_dbg |= 0x00000040

        self._logger.path("--Atn._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path(
            "++Atn._derived_process_mqtt_message %s", message.Payload.message.topic
        )
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
            case GameOn():
                self.log("Scada: Game On!")
                if self.latest_remaining_elec is not None:
                    self.log("Sending energy instruction with the latest remaining electricity")
                    self.send_energy_dispatches(self.latest_remaining_elec)
            case EventBase():
                path_dbg |= 0x00000020
                self._process_event(decoded.Payload)
                if (
                    decoded.Payload.TypeName
                    == ReportEvent.model_fields["TypeName"].default
                ):
                    path_dbg |= 0x00000040
                    self._process_report(decoded.Payload.Report)
                elif (
                    decoded.Payload.TypeName
                    == SnapshotSpaceheat.model_fields["TypeName"].default
                ):
                    path_dbg |= 0x00000080
                    self._process_snapshot(decoded.Payload)
                elif (
                    decoded.Payload.TypeName 
                    == RemainingElecEvent.model_fields['TypeName'].default
                ):
                    path_dbg |= 0x00000120
                    self.log(f"Received remaining electricity {decoded.Payload.Remaining.RemainingWattHours} Wh")
                    self.latest_remaining_elec = decoded.Payload.Remaining.RemainingWattHours
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
            if (
                telemetry_name == TelemetryName.WaterTempCTimes1000
                or telemetry_name == TelemetryName.WaterTempCTimes1000.value
            ):
                centigrade = single_reading.Value / 1000
                if self.settings.c_to_f:
                    fahrenheit = (centigrade * 9 / 5) + 32
                    extra = f"{fahrenheit:5.2f} F"
                else:
                    extra = f"{centigrade:5.2f} C"
            else:
                extra = f"{single_reading.Value} " f"{telemetry_name}"
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
        for reading in snapshot.LatestReadingList:
            self.latest_channel_values[reading.ChannelName] = reading.Value
        if self.is_simulated and self.temperature_channel_names is not None:
            for channel in self.temperature_channel_names:
                self.latest_channel_values[channel] = 60000

    def _process_layout_lite(self, layout: LayoutLite) -> None:
        self.ha1_params = layout.Ha1Params
        self.logger.error(f"Just got layout: {self.ha1_params}")
        if self.state == "DispatchDormantScadaNotReady":
            # ScadaReadyReceived: DispatchDormantScadaNotReady -> DispatchDormantScadaReady
            self.ScadaReadyReceived()
        self.log(f"State is now {self.state}")
        self.temperature_channel_names = [
            x.Name
            for x in layout.DataChannels
            if "depth" in x.Name and "micro-v" not in x.Name
        ]

    def _process_report(self, report: Report) -> None:
        self.data.latest_report = report
        # Check if HP is on or off by looking at relay 6
        for machine_state in report.StateList:
            ms : MachineStates = machine_state
            if f"relay{House0RelayIdx.hp_scada_ops}" in ms.MachineHandle:
                if ms.StateList[-1] == RelayClosedOrOpen.RelayOpen:
                    self.hp_is_off = True
                else:
                    self.hp_is_off = False
        if self.settings.save_events:
            report_file = (
                self.report_output_dir / f"Report.{report.SlotStartUnixS}.json"
            )
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
                Dst=self.scada.name,
                Payload=SendSnap(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                ),
            )
        )

    def send_new_params(self, new: Ha1Params) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=ScadaParams(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromName=H0N.atn,
                    ToName=H0N.home_alone,
                    UnixTimeMs=int(time.time() * 1000),
                    MessageId=str(uuid.uuid4()),
                    NewParams=new,
                ),
            )
        )

    def send_layout(self) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=SendLayout(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromName=H0N.atn,
                    ToName=H0N.primary_scada,
                ),
            )
        )
        self.log("Requesting layout")

    def take_control(self) -> float:
        """
        Will trigger Atn mode in scada, if the Scada gets this message
        and is in HomeAlone
        """
        if not self.state == "DispatchDormantScadaReady":
            self.log("Scada not ready! Not taking control")
            return
        elif not self.latest_channel_values:
            self.log("Not taking control! Do not have latest channel values")
            return
        # AtnWantsControl: DispatchDormantScadaReady -> DispatchLive
        self.AtnWantsControl()
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=DispatchContractGoLive(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    BlockchainSig="bogus_algo_sig",
                ),
            )
        )
        self.log(f"Wants control! State is now {self.state}")

    def release_control(self) -> float:
        """
        If scada is in Atn mode, will go to Homealone
        """
        if self.state == "DispatchLive":
            self.AtnReleasesControl()
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=DispatchContractGoDormant(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    BlockchainSig="bogus_algo_sig",
                ),
            )
        )

    def hack_oil_on(self) -> None:
        self.log("Sending HackOilOn to scada")
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=HackOilOn(),
            )
        )

    def hack_oil_off(self) -> None:
        self.log("Sending HackOilOff to scada")
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=HackOilOff(),
            )
        )
        
    def set_alpha(self, alpha: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "AlphaTimes10": int(alpha * 10)}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set alpha! {e}")

    def set_beta(self, beta: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "BetaTimes100": int(beta * 100)}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set beta! {e}")

    def set_gamma(self, gamma: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "GammaEx6": int(gamma * 1e6)}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set gamma! {e}")

    def set_intermediate_power(self, intermediate_power: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {
                        **self.ha1_params.model_dump(),
                        "IntermediatePowerKw": intermediate_power,
                    }
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set intermediate power! {e}")

    def set_intermediate_rswt(self, intermediate_rswt: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {
                        **self.ha1_params.model_dump(),
                        "IntermediateRswtF": int(intermediate_rswt),
                    }
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set intermediate rswt! {e}")

    def set_dd_power(self, dd_power: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "DdPowerKw": dd_power}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdPowerKw! {e}")

    def set_dd_rswt(self, dd_rswt: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "DdRswtF": dd_rswt}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdRswt! {e}")

    def set_dd_delta_t(self, dd_delta_t: float) -> None:
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "DdDeltaTF": dd_delta_t}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set DdDeltaTF! {e}")
    
    def set_load_overestimation_percent(self, load_overestimation_percent: float) -> None:
        if load_overestimation_percent < 0 or load_overestimation_percent > 100:
            self.log("Invalid entry, load_overestimation_percent should be a value between 0 and 100")
            return
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "LoadOverestimationPercent": load_overestimation_percent}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set LoadOverestimationPercent! {e}")

    def set_stratboss_dist_010(self, stratboss_dist_010v: int = 100) -> None:
        if stratboss_dist_010v < 0 or stratboss_dist_010v > 100:
            self.log("Invalid entry, stratboss_dist_010v should be a value between 0 and 100")
            return
        if self.ha1_params is None:
            self.send_layout()
        else:
            try:
                new = Ha1Params.model_validate(
                    {**self.ha1_params.model_dump(), "StratBossDist010": stratboss_dist_010v}
                )
                self.send_new_params(new)
            except Exception as e:
                self.logger.error(f"Failed to set LoadOverestimationPercent! {e}")

    def set_dist_010(self, val: int = 30) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.dist-010v",
                    AboutName="dist-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                ),
            )
        )

    def set_primary_010(self, val: int = 50) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.primary-010v",
                    AboutName="primary-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
                ),
            )
        )

    def set_store_010(self, val: int = 30) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.scada.name,
                Payload=AnalogDispatch(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    FromHandle="auto",
                    ToHandle="auto.store-010v",
                    AboutName="store-010v",
                    Value=val,
                    TriggerId=str(uuid.uuid4()),
                    UnixTimeMs=int(time.time() * 1000),
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
            command=command,
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
                Dst=self.scada.name,
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
        self.event_loop_thread = threading.Thread(
            target=asyncio.run, args=[self.run_forever()]
        )
        self.event_loop_thread.start()

    def stop_and_join_thread(self):
        self.stop()
        if self.event_loop_thread is not None and self.event_loop_thread.is_alive():
            self.event_loop_thread.join()

    def _start_derived_tasks(self):
        self._tasks.append(asyncio.create_task(self.main(), name="atn-main"))
        self._tasks.append(
            asyncio.create_task(self.fake_market_maker(), name="fake market maker")
        )
        self._tasks.append

    async def main(self):
        async with aiohttp.ClientSession() as session:
            await self.main_loop(session)

    async def main_loop(self, session: aiohttp.ClientSession) -> None:
        while not self._stop_requested:
            await asyncio.sleep(5)
            if datetime.now().minute >= 55 and not self.sent_bid:
                if self.state == "DispatchLive":
                    # In the last 5 minutes of the hour: make a bid for the next hour
                    try:
                        await self.run_d(session)
                    except Exception as e:
                        self.log(f"Exception running Dijkstra: {e}")
                else:
                    self.log(f"In the last 5 minutes but not running d. State is {self.state}")
            elif datetime.now().minute <= 55 and self.sent_bid:
                self.sent_bid = False
            else:
                self.log(f"Minute {datetime.now().minute}")
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    async def run_d(self, session: aiohttp.ClientSession) -> None:
        if self.sent_bid:
            self.log("NOT RUNNING Dijsktra! Already sent bid")
            return
        if datetime.now().minute >= 55:
            dijkstra_start_time = int(
                datetime.timestamp((datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0))
                )
        else:
            dijkstra_start_time = int(datetime.timestamp(datetime.now()))
            self.log("NOT RUNNING Dijkstra! Not in the last 5 minutes.")
            # TODO: under some conditions we might want to run a FLO at another time
            return
        await self.get_weather(session)
        self.get_price_update_forecast_usd_per_mwh()

        self.log("Finding thermocline position and top temperature")
        result = await self.get_thermocline_and_centroids()
        if result is None:
            self.log("Get thermocline and centroid failed! Releasing control of Scada!")
            self.release_control()
            return
        initial_toptemp, initial_bottomtemp, initial_thermocline = result

        buffer_available_kwh = await self.get_buffer_available_kwh()
        house_available_kwh = await self.get_house_available_kwh()

        flo_params = FloParamsHouse0(
            GNodeAlias=self.layout.scada_g_node_alias,
            StartUnixS=dijkstra_start_time,
            InitialTopTempF=int(initial_toptemp),
            InitialBottomTempF=int(initial_bottomtemp),
            InitialThermocline=initial_thermocline * 2,
            # TODO: price and weather forecasts should include the current hour if we are running a partial hour
            LmpForecast=self.price_forecast["lmp"],
            DistPriceForecast=self.price_forecast["dp"],
            RegPriceForecast=self.price_forecast["reg"],
            OatForecastF=self.weather_forecast["oat"],
            WindSpeedForecastMph=self.weather_forecast["ws"],
            AlphaTimes10=self.ha1_params.AlphaTimes10,
            BetaTimes100=self.ha1_params.BetaTimes100,
            GammaEx6=self.ha1_params.GammaEx6,
            IntermediatePowerKw=self.ha1_params.IntermediatePowerKw,
            IntermediateRswtF=self.ha1_params.IntermediateRswtF,
            DdPowerKw=self.ha1_params.DdPowerKw,
            DdRswtF=self.ha1_params.DdRswtF,
            DdDeltaTF=self.ha1_params.DdDeltaTF,
            MaxEwtF=self.ha1_params.MaxEwtF,
            HpIsOff=self.hp_is_off,
            BufferAvailableKwh=buffer_available_kwh,
            HouseAvailableKwh=house_available_kwh
        )
        self._links.publish_message(
            self.SCADA_MQTT, 
            Message(Src=self.publication_name, Dst="broadcast", Payload=flo_params)
        )
        self.log("Creating graph")
        st = time.time()
        g = DGraph(flo_params)
        self.log(f"The first time step is {round(g.params.fraction_of_hour_remaining*60)} minutes")
        self.log(f"Done in {round(time.time()-st,2)} seconds")
        self.log("Solving Dijkstra")
        g.solve_dijkstra()
        self.log("Solved!")
        self.log("Finding PQ pairs")
        st = time.time()
        pq_pairs: List[PriceQuantityUnitless] = g.generate_bid()
        self.log(
            f"Found {len(pq_pairs)} pairs in {round(time.time()-st,2)} seconds"
        )
        # TODO: remove this later
        if len(pq_pairs) > 100:
            self.log("TOO MANY PQ PAIRS!")

        # Generate bid
        t = time.time()
        slot_start_s = int(t - (t % 3600)) + 3600
        mtn = MarketTypeName.rt60gate5.value
        market_slot_name = f"e.{mtn}.{Atn.P_NODE}.{slot_start_s}"
        bid = AtnBid(
            BidderAlias=self.layout.atn_g_node_alias,
            MarketSlotName=market_slot_name,
            PqPairs=pq_pairs,
            InjectionIsPositive=False,  # withdrawing energy since load not generation
            PriceUnit=MarketPriceUnit.USDPerMWh,
            QuantityUnit=MarketQuantityUnit.AvgkW,
            SignedMarketFeeTxn="BogusAlgoSignature",
        )
        self._links.publish_message(
            self.SCADA_MQTT, 
            Message(Src=self.publication_name, Dst="broadcast", Payload=bid)
        )
        self.latest_bid = bid
        self.log(f"Bid: {bid}")
        self.sent_bid = True

    def latest_price_received(self, payload: LatestPrice) -> None:
        self.latest_price = payload
        self.log("Received latest price")
        if self.latest_bid is None:
            self.log("Ignoring - no bid exists")
            return
        if (
            datetime.now(self.timezone).minute != 0
            and datetime.now(self.timezone).second <= 5
        ):
            self.log(
                "The latest price was not received within the first 5 seconds of the hour. Abort."
            )
            return
        pq_pairs = [
            (x.PriceTimes1000, x.QuantityTimes1000) for x in self.latest_bid.PqPairs
        ]
        sorted_pq_pairs = sorted(pq_pairs, key=lambda pair: pair[0])
        # Quantity is AvgkW, so QuantityTimes1000 is avg_w
        assert self.latest_bid.QuantityUnit == MarketQuantityUnit.AvgkW
        for pair in sorted_pq_pairs:
            if pair[0] < payload.PriceTimes1000:
                avg_w = pair[1] # WattHours

        # 1 hour
        energy_wh = avg_w * 1
        if energy_wh < 1000:
            energy_wh = 0
        self.send_energy_dispatches(watthours=energy_wh, slot_minutes=60)

    def to_fahrenheit(self, t: float) -> float:
        return t * 9 / 5 + 32

    def fill_missing_store_temps(self):
        all_store_layers = sorted(
            [x for x in self.temperature_channel_names if "tank" in x]
        )
        for layer in all_store_layers:
            if (
                layer not in self.latest_temperatures
                or self.to_fahrenheit(self.latest_temperatures[layer] / 1000) < 70
                or self.to_fahrenheit(self.latest_temperatures[layer] / 1000) > 200
            ):
                self.latest_temperatures[layer] = None
        if H0CN.store_cold_pipe in self.latest_temperatures:
            value_below = self.latest_temperatures[H0CN.store_cold_pipe]
        else:
            value_below = 0
        for layer in sorted(all_store_layers, reverse=True):
            if self.latest_temperatures[layer] is None:
                self.latest_temperatures[layer] = value_below
            value_below = self.latest_temperatures[layer]
        self.latest_temperatures = {
            k: self.latest_temperatures[k] for k in sorted(self.latest_temperatures)
        }

    def get_latest_temperatures(self):
        if self.temperature_channel_names is None:
            self.temperatures_available = False
            self.log("Can't get latest temperatures, don't have temperature channel names!")
            return
        if not self.settings.is_simulated:
            temp = {
                x: self.latest_channel_values[x]
                for x in self.temperature_channel_names
                if x in self.latest_channel_values
                and self.latest_channel_values[x] is not None
            }
            self.latest_temperatures = temp.copy()
        else:
            self.log("IN SIMULATION - set all temperatures to 60 degC")
            self.latest_temperatures = {}
            for channel_name in self.temperature_channel_names:
                self.latest_temperatures[channel_name] = 60 * 1000
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
        else:
            self.temperatures_available = False
            all_buffer = [
                x for x in self.temperature_channel_names if "buffer-depth" in x
            ]
            available_buffer = [
                x for x in list(self.latest_temperatures.keys()) if "buffer-depth" in x
            ]
            if all_buffer == available_buffer:
                self.fill_missing_store_temps()
                self.temperatures_available = True

    async def get_RSWT(self, minus_deltaT=False):
        try:
            alpha = self.ha1_params.AlphaTimes10 / 10
            beta = self.ha1_params.BetaTimes100 / 100
            gamma = self.ha1_params.GammaEx6 / 1e6
            oat = self.weather_forecast["oat"][0]
            ws = self.weather_forecast["ws"][0]
            r = alpha + beta*oat + gamma*ws
            rhp= r if r>0 else 0
            intermediate_rswt = self.ha1_params.IntermediateRswtF
            dd_rswt = self.ha1_params.DdRswtF
            intermediate_power = self.ha1_params.IntermediatePowerKw
            dd_power = self.ha1_params.DdPowerKw
            no_power_rswt = -alpha/beta
            x_rswt = np.array([no_power_rswt, intermediate_rswt, dd_rswt])
            y_hpower = np.array([0, intermediate_power, dd_power])
            A = np.vstack([x_rswt**2, x_rswt, np.ones_like(x_rswt)]).T
            a, b, c = np.linalg.solve(A, y_hpower)
            c2 = c - rhp
            rswt = round((-b + (b**2-4*a*c2)**0.5)/(2*a),2)
            deltaT = self.ha1_params.DdDeltaTF/self.ha1_params.DdPowerKw * (a*rswt**2 + b*rswt + c)
            deltaT = deltaT if deltaT>0 else 0
            if minus_deltaT:
                return rswt - deltaT
            return rswt
        except:
            self.log("Could not find RSWT!")
            return None

    async def get_thermocline_and_centroids(self) -> Optional[Tuple[float, int]]:
        # Get all tank temperatures in a dict, if you can't abort
        if self.temperature_channel_names is None:
            self.send_layout()
            await asyncio.sleep(5)
        self.get_latest_temperatures()
        if not self.temperatures_available:
            self.log(
                "Not enough tank temperatures available to compute top temperature and thermocline!"
            )
            return None
        all_store_layers = sorted(
            [x for x in self.temperature_channel_names if "tank" in x]
        )
        try:
            tank_temps = {
                key: self.to_fahrenheit(self.latest_temperatures[key] / 1000)
                for key in all_store_layers
            }
        except KeyError as e:
            self.log(
                f"Failed to get all the tank temps in get_thermocline_and_centroids! Bailing on process {e}"
            )
            return None
        # Process the temperatures before clustering
        processed_temps = []
        for key in tank_temps:
            processed_temps.append(tank_temps[key])
        iter_count = 0
        while (
            sorted(processed_temps, reverse=True) != processed_temps and iter_count < 20
        ):
            iter_count += 1
            processed_temps = []
            for key in tank_temps:
                if processed_temps:
                    if tank_temps[key] > processed_temps[-1]:
                        mean = round((processed_temps[-1] + tank_temps[key]) / 2)
                        processed_temps[-1] = mean
                        processed_temps.append(mean)
                    else:
                        processed_temps.append(tank_temps[key])
                else:
                    processed_temps.append(tank_temps[key])
            i = 0
            for key in tank_temps:
                tank_temps[key] = processed_temps[i]
                i += 1
            if iter_count == 20:
                processed_temps = sorted(processed_temps, reverse=True)
        # Cluster
        data = processed_temps.copy()
        labels = self.kmeans(data, k=2)
        cluster_top = sorted([data[i] for i in range(len(data)) if labels[i] == 0])
        cluster_bottom = sorted([data[i] for i in range(len(data)) if labels[i] == 1])
        if not cluster_top:
            cluster_top = cluster_bottom.copy()
            cluster_bottom = []
        if cluster_bottom:
            if max(cluster_bottom) > max(cluster_top):
                cluster_top_copy = cluster_top.copy()
                cluster_top = cluster_bottom.copy()
                cluster_bottom = cluster_top_copy
        thermocline = len(cluster_top)
        top_centroid_f = round(sum(cluster_top) / len(cluster_top), 3)
        if cluster_bottom:
            bottom_centroid_f = round(sum(cluster_bottom) / len(cluster_bottom), 3)
        else:
            bottom_centroid_f = min(cluster_top)
        # Process clustering
        self.log(f"Thermocline {thermocline}, top: {top_centroid_f} F, bottom: {bottom_centroid_f} F")
        try:
            rswt = await self.get_RSWT()
            self.log(f"RSWT = {rswt} F")
            if top_centroid_f < rswt and max(processed_temps) >= rswt:
                print("There is water available above RSWT, changing the clustering result")
                top_cluster = [x for x in processed_temps if x>=rswt]
                bottom_cluster = [x for x in processed_temps if x<rswt]
                thermocline = len(top_cluster) #check this
                top_centroid_f = round(sum(top_cluster)/len(top_cluster),3)
                bottom_centroid_f = round(sum(bottom_cluster)/len(bottom_cluster),3)
        except Exception as e:
            self.log(f"Could not process clustering results! Error: {e}")
        # TODO: post top_centroid, thermocline, bottom_centroid as synthetic channels
        self.log(f"Thermocline {thermocline}, top: {top_centroid_f} F, bottom: {bottom_centroid_f} F")
        return top_centroid_f, bottom_centroid_f, thermocline
    
    async def get_buffer_available_kwh(self):
        if self.temperature_channel_names is None:
            self.send_layout()
            await asyncio.sleep(5)
        self.get_latest_temperatures()
        buffer_temperatures = {k: self.to_fahrenheit(v/1000)
                               for k,v in self.latest_temperatures.items() 
                               if 'buffer' in k
                               and v is not None}
        if not buffer_temperatures:
            self.log(f"Missing temperatures in get_buffer_available_kwh, returning 0 kWh")
            return 0
        try:
            rswt = await self.get_RSWT(minus_deltaT=False)
            rswt_minus_deltaT = await self.get_RSWT(minus_deltaT=True)
            m_layer_kg = 120/4 * 3.785
            buffer_available_energy = 0
            for bl in buffer_temperatures:
                if buffer_temperatures[bl] >= rswt:
                    buffer_available_energy += m_layer_kg * 4.187/3600 * (buffer_temperatures[bl]-rswt_minus_deltaT) * 5/9
            if round(buffer_available_energy,2) == 0:
                for bl in buffer_temperatures:
                    buffer_available_energy += - m_layer_kg * 4.187/3600 * (rswt - buffer_temperatures[bl]) * 5/9
            return round(buffer_available_energy,2)
        except Exception as e:
            self.log(f"Something failed in get_buffer_available_kwh ({e}), returning 0 kWh")
            return 0
        
    async def get_house_available_kwh(self):
        # Thermal mass of house? In kWh/degF
        # How much thermal mass is one zone?
        return 0
    
    def use_oil_as_fuel_substitute(self) -> False:
        if self.latest_price is None:
            return False
        if self.latest_price.PriceUnit != MarketPriceUnit.USDPerMWh:
            raise Exception(f"Stop being so parochial and assuming {MarketPriceUnit.USDPerMWh}")
        price_usd_per_mwh = self.latest_price.PriceTimes1000 / 1000
        self.log(f"Latest price is ${price_usd_per_mwh}/MWh. Fuel sub threshold ${self.settings.fuel_sub_usd_per_mwh}/MWh")
        if price_usd_per_mwh > self.settings.fuel_sub_usd_per_mwh and self.settings.fuel_substitution:
            return True
        elif not self.settings.fuel_substitution:
            self.log("fuel_substation variable set to False! ")
            return False
        return False

    def send_energy_dispatches(self, watthours: int, slot_minutes: int = 60) -> None:
        """ Sends an energy instructions  at the top of the next 5 minutes.

         - EnergyInstruction for electricity. 
         - HackOilOn and/or HackOilOff

         If deciding to turn on oil, sends an EnergyInstruction of 0 instead of watthours
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                self._wait_and_send_energy_dispatches(watthours, slot_minutes)
            )
        else:
            loop.run_until_complete(self._wait_and_send_energy_dispatches(watthours, slot_minutes))
    
    async def _wait_and_send_energy_dispatches(self, watthours: int, slot_minutes: int=60) -> None:
        """ Sends an energy instructions  at the top of the next 5 minutes.

         - EnergyInstruction for electricity. 
         - HackOilOn and/or HackOilOff

         If deciding to turn on oil, sends an EnergyInstruction of 0 instead of watthours
        """
        if self.latest_price is None:
            self.log("Don't have a latest price. Not sending energy instruction")
            # TODO: ignore if latest price is stale (no longer in market slot)
            return
        after_top_s = (time.time() % 300)
        # EnergyInstructions must be sent within 10 seconds of the top of 5 minutes
        if after_top_s > 5:
            wait_s = 300 - after_top_s
            self.log(f"Sleeping {wait_s} seconds before sending EnergyInstruction")
            await asyncio.sleep(300 - (time.time() % 300)) # wait until the top of 5 minutes

        t = time.time()
        slot_start_s = int(t - (t % 300))
        if watthours > 0 and self.use_oil_as_fuel_substitute():
            watthours = 0
            if watthours > 2500:
                self.hack_oil_on()
            else:
                self.hack_oil_off() # Hack for right now. If more expensive than oil use the thermal store of house            
        else:
            self.hack_oil_off()
        try:
            payload = EnergyInstruction(
                FromGNodeAlias=self.layout.atn_g_node_alias,
                SlotStartS=slot_start_s,
                SlotDurationMinutes=slot_minutes,
                SendTimeMs=int(time.time() * 1000),
                AvgPowerWatts=int(watthours) if watthours>=0 else 0,
            )
            self.payload = payload
            self.send_threadsafe(
                Message(
                    Src=self.name,
                    Dst=self.scada.name,
                    Payload=payload,
                )
            )
            self.log(f"Sent EnergyInstruction: {payload}")

        except Exception as e:
            self.log(f"Missed the boat sending this energy instruction!:{e} ")

    async def get_weather(self, session: aiohttp.ClientSession) -> None:
        config_dir = self.settings.paths.config_dir
        weather_file = config_dir / "weather.json"
        try:
            url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
            response =  await session.get(url)
            if response.status != 200:
                self.log(f"Error fetching weather data: {response.status}")
                return None
            data = await response.json()
            forecast_hourly_url = data["properties"]["forecastHourly"]
            forecast_response = await session.get(forecast_hourly_url)
            if forecast_response.status != 200:
                self.log(
                    f"Error fetching hourly weather forecast: {forecast_response.status}"
                )
                return None
            forecast_data = await forecast_response.json()
            forecasts = {}
            periods = forecast_data["properties"]["periods"]
            for period in periods:
                if (
                    "temperature" in period
                    and "startTime" in period
                    and datetime.fromisoformat(period["startTime"])
                    > datetime.now(tz=self.timezone)
                ):
                    forecasts[datetime.fromisoformat(period["startTime"])] = period[
                        "temperature"
                    ]
            forecasts = dict(list(forecasts.items())[:96])
            cropped_forecast = dict(list(forecasts.items())[:48])
            wf = {
                "time": list(cropped_forecast.keys()),
                "oat": list(cropped_forecast.values()),
                "ws": [0] * len(cropped_forecast),
            }
            self.log(
                f"Obtained a {len(forecasts)}-hour weather forecast starting at {wf['time'][0]}"
            )
            weather_long = {
                "time": [x.timestamp() for x in list(forecasts.keys())],
                "oat": list(forecasts.values()),
                "ws": [0] * len(forecasts),
            }
            with open(weather_file, "w") as f:
                json.dump(weather_long, f, indent=4)

        except Exception as e:
            self.log(f"[!] Unable to get weather forecast from API: {e}")
            try:
                with open(weather_file, "r") as f:
                    weather_long = json.load(f)
                    weather_long["time"] = [
                        datetime.fromtimestamp(x, tz=self.timezone)
                        for x in weather_long["time"]
                    ]
                if weather_long["time"][-1] >= datetime.fromtimestamp(
                    time.time(), tz=self.timezone
                ) + timedelta(hours=48):
                    self.log("A valid weather forecast is available locally.")
                    time_late = weather_long["time"][0] - datetime.now(self.timezone)
                    hours_late = int(time_late.total_seconds() / 3600)
                    wf = weather_long
                    for key in wf:
                        wf[key] = wf[key][hours_late : hours_late + 48]
                else:
                    self.log(
                        "No valid weather forecasts available locally. Using coldest of the current month."
                    )
                    current_month = datetime.now().month - 1
                    wf = {
                        "time": [
                            datetime.now(tz=self.timezone) + timedelta(hours=1 + x)
                            for x in range(48)
                        ],
                        "oat": [self.coldest_oat_by_month[current_month]] * 48,
                        "ws": [0] * 48,
                    }
            except Exception as e:
                self.log(
                    "No valid weather forecasts available locally. Using coldest of the current month."
                )
                current_month = datetime.now().month - 1
                wf = {
                    "time": [
                        datetime.now(tz=self.timezone) + timedelta(hours=1 + x)
                        for x in range(48)
                    ],
                    "oat": [self.coldest_oat_by_month[current_month]] * 48,
                    "ws": [0] * 48,
                }

        self.weather_forecast = {
            "oat": wf["oat"],
            "ws": wf["ws"],
        }

    def get_price_update_forecast_usd_per_mwh(self) -> float:
        """ returns price this hour and updates self.price_forecast for the start of next hour

        All in $/MWh
        """
        # Read the 72h electricity prices from local CSV file
        # TODO: replace with a price service
        dist_usd_mwh = []
        lmp_usd_mwh = []
        reg_usd_mwh = [0]*72
        try:
            house_alias = self.layout.scada_g_node_alias.split('.')[-2]
            file_path = f"/home/ubuntu/{house_alias}-atn/gw-scada-spaceheat-python/price_forecast.csv"
            with open(file_path, mode='r', newline='') as file:
                reader = csv.reader(file)
                header = next(reader)
                for row in reader:
                    dist_usd_mwh.append(float(row[0]))
                    lmp_usd_mwh.append(float(row[1]))
                if len(dist_usd_mwh)<72 or len(lmp_usd_mwh)<72:
                    raise Exception("Price forecasts must be at least 72 hours long")
        except Exception as e:
            self.log("Error reading price forecast from csv")
            raise Exception(e)

        dp_forecast_usd_per_mwh = dist_usd_mwh[datetime.now(tz=self.timezone).hour+1:datetime.now(tz=self.timezone).hour+49]
        lmp_forecast_usd_per_mwh = lmp_usd_mwh[datetime.now(tz=self.timezone).hour+1:datetime.now(tz=self.timezone).hour+49]
        reg_forecast_usd_per_mwh = reg_usd_mwh[datetime.now(tz=self.timezone).hour+1:datetime.now(tz=self.timezone).hour+49]
        self.price_forecast = {
            "dp": dp_forecast_usd_per_mwh,
            "lmp": lmp_forecast_usd_per_mwh,
            "reg": reg_forecast_usd_per_mwh,
        }
        self.log("Succesfully read price forecast from local CSV")
        self.log(self.price_forecast)
        total_price = [dp+lmp+reg for dp,lmp,reg in zip(dist_usd_mwh, lmp_usd_mwh, reg_usd_mwh)]
        return total_price[datetime.now(tz=self.timezone).hour]

    def kmeans(self, data, k=2, max_iters=100, tol=1e-4):
        data = np.array(data).reshape(-1, 1)
        centroids = data[np.random.choice(len(data), k, replace=False)]
        for _ in range(max_iters):
            labels = np.argmin(np.abs(data - centroids.T), axis=1)
            new_centroids = np.zeros_like(centroids)
            for i in range(k):
                cluster_points = data[labels == i]
                if len(cluster_points) > 0:
                    new_centroids[i] = cluster_points.mean()
                else:
                    new_centroids[i] = data[np.random.choice(len(data))]
            if np.all(np.abs(new_centroids - centroids) < tol):
                break
            centroids = new_centroids
        return labels


    async def fake_market_maker(self):
        while True:
            # Calculate the time to the next top of the hour
            now = time.time()
            next_top_of_hour = (
                int(now // 3600) + 1
            ) * 3600  # next top of the hour in seconds
            sleep_time = next_top_of_hour - now

            # Sleep until the top of the hour
            await asyncio.sleep(sleep_time)
            self.send_latest_price()

    def send_latest_price(self) -> float:
        now = time.time()
        slot_start_s = int(now) - int(now) % 3600
        mtn = MarketTypeName.rt60gate5.value
        market_slot_name = f"e.{mtn}.{Atn.P_NODE}.{slot_start_s}"
        usd_per_mwh = self.get_price_update_forecast_usd_per_mwh()
        price = LatestPrice(
                FromGNodeAlias=Atn.P_NODE,
                PriceTimes1000=int(usd_per_mwh * 1000),
                PriceUnit=MarketPriceUnit.USDPerMWh,
                MarketSlotName=market_slot_name,
                MessageId=str(uuid.uuid4()),
            )
        self.log(f"Trying to Broadcasting price(x1000) {usd_per_mwh} at the top of the hour.")
        try:
            self.send_threadsafe(
                Message(Src=self.name, Dst=self.name, Payload=price)
            )
        except Exception as e:
            self.log(f"Problem generating or sending a LatestPrice: {e}")



    def log(self, note: str) -> None:
        log_str = f"[atn] {note}"
        self.services.logger.error(log_str)

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
