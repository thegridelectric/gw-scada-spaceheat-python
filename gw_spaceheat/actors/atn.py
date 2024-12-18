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
from typing import List, Dict, cast
from datetime import datetime, timedelta
import pytz
import requests
import json

from gwproactor.links.link_settings import LinkSettings
from data_classes.house_0_names import H0CN
from gwproto.named_types import SendSnap
from paho.mqtt.client import MQTTMessageInfo
import rich
from pydantic import BaseModel

from gwproto import create_message_model
from gwproto import MQTTCodec
from data_classes.house_0_layout import House0Layout
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
from named_types import (DispatchContractGoDormant, DispatchContractGoLive, Ha1Params, 
                        LayoutLite, ScadaParams, SendLayout)

from gwproactor import ServicesInterface
import asyncio
import time
import numpy as np
from datetime import datetime
from gwproto import Message
from result import Ok, Result
from typing import List, Tuple
from actors.scada_actor import ScadaActor
from gw.enums import MarketTypeName
from enums import MarketPriceUnit, MarketQuantityUnit
from named_types import AtnBid, EnergyInstruction, LatestPrice, Ha1Params
from named_types.price_quantity_unitless import PriceQuantityUnitless
from actors.scada_data import ScadaData
from actors.flo import DGraph, FloParamsHouse0
from actors.synth_generator import WeatherForecast, PriceForecast
from data_classes.house_0_names import H0CN
from gwproto.named_types import SingleReading


class AtnMQTTCodec(MQTTCodec):
    exp_src: str
    exp_dst: str = H0N.atn

    def __init__(self, hardware_layout: House0Layout):
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
    layout: House0Layout
    my_channels: List[DataChannel]
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_report: Optional[Report] = None

    def __init__(self, layout: House0Layout):
        self.layout=layout
        self.my_channels = list(layout.data_channels.values())
        self.latest_snapshot = None
        self.latest_report = None


class Atn(ActorInterface, Proactor):
    MAIN_LOOP_SLEEP_SECONDS = 120
    P_NODE = "hw1.isone.ver.keene"
    SCADA_MQTT = "scada"
    data: AtnData
    event_loop_thread: Optional[threading.Thread] = None
    dashboard: Optional[Dashboard]
    ha1_params: Optional[Ha1Params]

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: House0Layout,
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
        self.is_simulated = self.settings.is_simulated
        self.latest_channel_values: Dict[str, int] = {}
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.latitude = self.settings.latitude
        self.longitude = self.settings.longitude
        self.sent_bid = False
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
    def layout(self) -> House0Layout:
        return cast(House0Layout, self._layout)

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
            case DispatchContractGoDormant():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload)
            case DispatchContractGoLive():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload)
            case EnergyInstruction():
                path_dbg |= 0x00000080
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
        for reading in snapshot.LatestReadingList:
            self.latest_channel_values[reading.ChannelName] = reading.Value
        if self.is_simulated and self.temperature_channel_names is not None:
            for channel in self.temperature_channel_names:
                self.latest_channel_values[channel] = 60000
        self.log("Received and processed a SnapShot")

    def _process_layout_lite(self, layout: LayoutLite) -> None:
        self.ha1_params = layout.Ha1Params
        self.logger.error(f"Just got layout: {self.ha1_params}")
        self.temperature_channel_names = [
            x.Name for x in layout.DataChannels 
            if 'depth' in x.Name and 'micro-v' not in x.Name]
        self.log(self.temperature_channel_names)

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
        self.log("Requesting layout")

    def take_control(self) -> float:
        """
        Will trigger Atn mode in scada, if the Scada gets this message
        and is in HomeAlone
        """
        self.send_threadsafe(
            Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=DispatchContractGoLive(
                            FromGNodeAlias=self.layout.atn_g_node_alias,
                            BlockchainSig="bogus_algo_sig"
                        ),
                    )
        )

    def release_control(self) -> float:
        """
        If scada is in Atn mode, will go to Homealone
        """
        self.send_threadsafe(
            Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=DispatchContractGoDormant(
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
        self._tasks.append(
            asyncio.create_task(self.fake_market_maker(), name="fake market maker")
        )

    async def main(self):
        while not self._stop_requested:
            await asyncio.sleep(5)
            while self.ha1_params is None:
                self.send_layout()
                await asyncio.sleep(2)
            while not self.latest_channel_values:
                self.log("Waiting for a snapshot")
                await asyncio.sleep(15)  
            try:
                self.run_d()
            except Exception as e:
                self.log(f"Exception running Dijkstra: {e}")   
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS) 

    def run_d(self)-> None:
        # In the last 5 minutes of the hour: make a bid for the next hour
        if datetime.now().minute >= 55 and not self.sent_bid:

            self.get_weather_forecast()
            self.get_price_forecast()
                        
            self.log("Finding thermocline position and top temperature")
            initial_toptemp, initial_thermocline = self.get_thermocline_and_centroids()
            if (initial_toptemp, initial_thermocline) is None:
                self.log("Can not run Dijkstra. Releasing control of Scada!")
                self.release_control()
                return

            configuration = FloParamsHouse0(
                StartUnixS = int(datetime.timestamp((datetime.now()+timedelta(hours=1)).replace(minute=0,second=0,microsecond=0))),
                InitialTopTemp = initial_toptemp,
                InitialThermocline = initial_thermocline * 2,
                DpForecastUsdMwh = self.price_forecast['dp'],
                LmpForecastUsdMwh = self.price_forecast['lmp'],
                OatForecastF = self.weather_forecast['oat'],
                WindSpeedForecastMph = self.weather_forecast['ws'],
                AlphaTimes10 = self.ha1_params.AlphaTimes10,
                BetaTimes100 = self.ha1_params.BetaTimes100,
                GammaEx6 = self.ha1_params.GammaEx6,
                IntermediatePowerKw = self.ha1_params.IntermediatePowerKw,
                IntermediateRswtF = self.ha1_params.IntermediateRswtF,
                DdPowerKw = self.ha1_params.DdPowerKw,
                DdRswtF = self.ha1_params.DdRswtF,
                DdDeltaTF = self.ha1_params.DdDeltaTF,
                MaxEwtF = self.ha1_params.MaxEwtF
            )

            self.log("Creating graph")
            st = time.time()
            g = DGraph(configuration)
            self.log(f"Done in {round(time.time()-st,2)} seconds")
            self.log("Solving Dijkstra")
            g.solve_dijkstra()
            self.log("Solved!")
            self.log("Finding PQ pairs")
            st = time.time()
            pq_pairs: List[PriceQuantityUnitless] = g.generate_bid()
            self.log(f"Found {len(pq_pairs)} pairs in {round(time.time()-st,2)} seconds")
            # TODO: remove this later
            if len(pq_pairs) > 100:
                self.log("TOO MANY PQ PAIRS!")

            # Generate bid
            t = time.time()
            slot_start_s = int(t-(t%3600))
            mtn = MarketTypeName.rt60gate5.value
            market_slot_name = f"e.{mtn}.{Atn.P_NODE}.{slot_start_s}"
            bid = AtnBid(
                BidderAlias=self.layout.atn_g_node_alias,
                MarketSlotName=market_slot_name,
                PqPairs=pq_pairs,
                InjectionIsPositive=False, # withdrawing energy since load not generation
                PriceUnit=MarketPriceUnit.USDPerMWh,
                QuantityUnit=MarketQuantityUnit.AvgkW,
                SignedMarketFeeTxn="BogusAlgoSignature"
            )
            self.log(f"Bid: {bid}")
            self.sent_bid = True

        elif datetime.now().minute <= 55 and self.sent_bid:
            self.sent_bid = False
        else:
            self.log(f"Minute {datetime.now().minute}")

    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32
    
    def fill_missing_store_temps(self):
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        for layer in all_store_layers:
            if (layer not in self.latest_temperatures 
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) < 70
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) > 200):
                self.latest_temperatures[layer] = None
        if H0CN.store_cold_pipe in self.latest_temperatures:
            value_below = self.latest_temperatures[H0CN.store_cold_pipe]
        else:
            value_below = 0
        for layer in sorted(all_store_layers, reverse=True):
            if self.latest_temperatures[layer] is None:
                self.latest_temperatures[layer] = value_below
            value_below = self.latest_temperatures[layer]  
        self.latest_temperatures = {k:self.latest_temperatures[k] for k in sorted(self.latest_temperatures)}

    def get_latest_temperatures(self):
        if self.temperature_channel_names is None:
            self.temperatures_available = False
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
            all_buffer = [x for x in self.temperature_channel_names if 'buffer-depth' in x]
            available_buffer = [x for x in list(self.latest_temperatures.keys()) if 'buffer-depth' in x]
            if all_buffer == available_buffer:
                self.fill_missing_store_temps()
                self.temperatures_available = True

    def get_thermocline_and_centroids(self) -> Optional[Tuple[float, int]]:
        # Get all tank temperatures in a dict, if you can't abort
        self.get_latest_temperatures()
        if not self.temperatures_available:
            self.log("Not enough tank temperatures available to compute top temperature and thermocline!")
            return None
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        try:
            tank_temps = {key: self.to_fahrenheit(self.latest_temperatures[key]/1000) for key in all_store_layers}
        except KeyError as e:
            self.log(f"Failed to get all the tank temps in get_thermocline_and_centroids! Bailing on process {e}")
            return None
        # Process the temperatures before clustering
        processed_temps = []
        for key in tank_temps:
            processed_temps.append(tank_temps[key])
        iter_count = 0
        while sorted(processed_temps, reverse=True) != processed_temps and iter_count<20:
            iter_count+=1
            processed_temps = []
            for key in tank_temps:
                if processed_temps:
                    if tank_temps[key] > processed_temps[-1]:
                        mean = round((processed_temps[-1] + tank_temps[key])/2)
                        processed_temps[-1] = mean
                        processed_temps.append(mean)
                    else:
                        processed_temps.append(tank_temps[key])
                else:
                    processed_temps.append(tank_temps[key])
            i = 0
            for key in tank_temps:
                tank_temps[key] = processed_temps[i]
                i+=1
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
        top_centroid_f = round(sum(cluster_top)/len(cluster_top),3)
        if cluster_bottom:
            bottom_centroid_f = round(sum(cluster_bottom)/len(cluster_bottom),3)
        else:
            bottom_centroid_f = min(cluster_top)
        self.log(f"Thermocline {thermocline}, top: {top_centroid_f} F, bottom: {bottom_centroid_f} F")
        # TODO: post top_centroid, thermocline, bottom_centroid as synthetic channels
        return top_centroid_f, thermocline

    def send_energy_instr(self, watthours: int, slot_minutes: int = 60):
        # wait until the top of the 5 minutes
        t = time.time()
        wait_s = 300 - t%300
        time.sleep(wait_s)
        t = time.time()
        slot_start_s = int(t - (t % 300))
        # EnergyInstructions must be sent within 10 seconds of the top of 5 minutes
        if t - slot_start_s < 10:
            payload = EnergyInstruction(
                        FromGNodeAlias=self.layout.atn_g_node_alias,
                        SlotStartS=slot_start_s,
                        SlotDurationMinutes=slot_minutes,
                        SendTimeMs=int(time.time()*1000),
                        AvgPowerWatts=int(watthours)
                    )
            self.payload = payload
            self.log(f"Sent EnergyInstruction: {payload}")
            self.send_threadsafe(
                Message(
                    Src=self.name,
                    Dst=self.name,
                    Payload=payload,
                )
            )

    def get_weather_forecast(self) -> None:
        config_dir = self.settings.paths.config_dir
        weather_file = config_dir / "weather.json"
        try:
            url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
            response = requests.get(url)
            if response.status_code != 200:
                self.log(f"Error fetching weather data: {response.status_code}")
                return None
            data = response.json()
            forecast_hourly_url = data['properties']['forecastHourly']
            forecast_response = requests.get(forecast_hourly_url)
            if forecast_response.status_code != 200:
                self.log(f"Error fetching hourly weather forecast: {forecast_response.status_code}")
                return None
            forecast_data = forecast_response.json()
            forecasts = {}
            periods = forecast_data['properties']['periods']
            for period in periods:
                if ('temperature' in period and 'startTime' in period 
                    and datetime.fromisoformat(period['startTime'])>datetime.now(tz=self.timezone)):
                    forecasts[datetime.fromisoformat(period['startTime'])] = period['temperature']
            forecasts = dict(list(forecasts.items())[:96])
            cropped_forecast = dict(list(forecasts.items())[:48])
            wf = {
                'time': list(cropped_forecast.keys()),
                'oat': list(cropped_forecast.values()),
                'ws': [0]*len(cropped_forecast)
                }
            self.log(f"Obtained a {len(forecasts)}-hour weather forecast starting at {wf['time'][0]}")
            weather_long = {
                'time': [x.timestamp() for x in list(forecasts.keys())],
                'oat': list(forecasts.values()),
                'ws': [0]*len(forecasts)
                }
            with open(weather_file, 'w') as f:
                json.dump(weather_long, f, indent=4) 
        
        except Exception as e:
            self.log(f"[!] Unable to get weather forecast from API: {e}")
            try:
                with open(weather_file, 'r') as f:
                    weather_long = json.load(f)
                    weather_long['time'] = [datetime.fromtimestamp(x, tz=self.timezone) for x in weather_long['time']]
                if weather_long['time'][-1] >= datetime.fromtimestamp(time.time(), tz=self.timezone)+timedelta(hours=48):
                    self.log("A valid weather forecast is available locally.")
                    time_late = weather_long['time'][0] - datetime.now(self.timezone)
                    hours_late = int(time_late.total_seconds()/3600)
                    wf = weather_long
                    for key in wf:
                        wf[key] = wf[key][hours_late:hours_late+48]
                else:
                    self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                    current_month = datetime.now().month-1
                    wf = {
                        'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(48)],
                        'oat': [self.coldest_oat_by_month[current_month]]*48,
                        'ws': [0]*48,
                        }
            except Exception as e:
                self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                current_month = datetime.now().month-1
                wf = {
                    'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(48)],
                    'oat': [self.coldest_oat_by_month[current_month]]*48,
                    'ws': [0]*48,
                    }

        self.weather_forecast = {
            'oat': wf['oat'], 
            'ws': wf['ws'],
            }

    def get_price_forecast(self) -> None:
        daily_dp = [50.13]*7 + [487.63]*5 + [54.98]*4 + [487.63]*4 + [50.13]*4
        dp_forecast_usd_per_mwh = (daily_dp[datetime.now(tz=self.timezone).hour+1:] + daily_dp[:datetime.now(tz=self.timezone).hour+1])*2
        lmp_forecast_usd_per_mwh = [102]*48
        self.price_forecast = {
            'dp': dp_forecast_usd_per_mwh,
            'lmp': lmp_forecast_usd_per_mwh
            }
        
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

    def get_price(self) -> float:
        # Daily price pattern for distribution (Versant TOU tariff)
        daily_dp = [50.13]*7 + [487.63]*5 + [54.98]*4 + [487.63]*4 + [50.13]*4
        # LMP price pattern 
        daily_lmp = [102]*48  # Or use another pattern as needed

        price_by_hr = [dp + lmp for dp, lmp in zip(daily_dp, daily_lmp)]
        current_hour = datetime.now(tz=self.timezone).hour
        return price_by_hr[(current_hour - 1) % len(price_by_hr)]
    
    async def broadcast_price(self):
        while True:
            # Calculate the time to the next top of the hour
            now = time.time()
            next_top_of_hour = (int(now // 3600) + 1) * 3600  # next top of the hour in seconds
            sleep_time = next_top_of_hour - now
            
            # Sleep until the top of the hour
            await asyncio.sleep(sleep_time)
            now = time.time()
            slot_start_s = int(now) - int(now) % 300
            mtn = MarketTypeName.rt60gate5.value
            market_slot_name = f"e.{mtn}.{Atn.P_NODE}.{slot_start_s}"

            price = LatestPrice(
                FromGNodeAlias="hw1.isone.me.versant.keene",
                PriceTimes1000=3,
                PriceUnit=MarketPriceUnit.USDPerMWh,
                MarketSlotName=market_slot_name,
                MessageId=str(uuid.uuid4())
            )
            print("Broadcasting price at the top of the hour.")

    async def fake_market_maker(self) -> None:


    def log(self, note: str) ->None:
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
