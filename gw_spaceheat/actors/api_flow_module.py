import json
import math
import time
from functools import cached_property
from typing import Dict, List, Literal, Optional
from gw.errors import DcError
import numpy as np
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from gwproactor import Actor, Problems, ServicesInterface
from gwproto import Message
from gwproto.message import Header
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.components import PicoFlowModuleComponent
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import MakeModel, HzCalcMethod, GpmFromHzMethod, TelemetryName
from gwproto.types import ComponentAttributeClassGt as CacGt
from gwproto.types import ComponentGt, ChannelReadings, SingleReading, SyncedReadings
from gwproto.types import TicklistHall, TicklistReed, TicklistHallReport, TicklistReedReport
from gwproto.types.web_server_gt import DEFAULT_WEB_SERVER_NAME
from pydantic import BaseModel
from gwproactor import QOS
from result import Ok, Result
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt


class FlowHallParams(BaseModel):
    HwUid: str
    ActorNodeName: str
    FlowNodeName: str
    PublishTicklistPeriodS: int
    PublishEmptyTicklistAfterS: int
    TypeName: Literal["flow.hall.params"]
    Version: Literal["101"] = "101"

class FlowReedParams(BaseModel):
    HwUid: str
    ActorNodeName: str
    FlowNodeName: str
    PublishTicklistLength: int
    PublishAnyTicklistAfterS: int
    DeadbandMilliseconds: int
    TypeName: Literal["flow.reed.params"]
    Version: Literal["101"] = "101"


class ApiFlowModule(Actor):

    _component: PicoFlowModuleComponent
    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        super().__init__(name, services)
        component = services.hardware_layout.component(name)
        if not isinstance(component, PicoFlowModuleComponent):
            display_name = getattr(
                component.gt, "display_name", "MISSING ATTRIBUTE display_name"
            )
            raise ValueError(
                f"ERROR. Component <{display_name}> has type {type(component)}. "
                f"Expected PicoComponent.\n"
                f"  Node: {self.name}\n"
                f"  Component id: {component.gt.ComponentId}"
            )
        self.layout = self.services.hardware_layout
        self._component = component
        self._hw_uid = self._component.gt.HwUid
        self.nano_timestamps: List[int] = [] # nanoseconds
        self.latest_hz = None
        self.latest_gpm = None
        self.latest_gallons = 0

        self.gpm_channel = self.layout.data_channels[f"{self.name}"]
        self.hz_channel = self.layout.data_channels[f"{self.name}-hz"]

        self.validate_config_params(self)
        if self._component.gt.Enabled:
            if self._component.cac.MakeModel == MakeModel.GRIDWORKS__PICOFLOWHALL:
                self._services.add_web_route(
                    server_name=DEFAULT_WEB_SERVER_NAME,
                    method="POST",
                    path="/" + self.hall_params_path,
                    handler=self._handle_hall_params_post,
                )
                self._services.add_web_route(
                    server_name=DEFAULT_WEB_SERVER_NAME,
                    method="POST",
                    path="/" + self.ticklist_hall_path,
                    handler=self._handle_ticklist_hall_post,
                )
            elif self._component.cac.MakeModel == MakeModel.GRIDWORKS__PICOFLOWREED:
                self._services.add_web_route(
                    server_name=DEFAULT_WEB_SERVER_NAME,
                    method="POST",
                    path="/" + self.reed_params_path,
                    handler=self._handle_reed_params_post,
                )
                self._services.add_web_route(
                    server_name=DEFAULT_WEB_SERVER_NAME,
                    method="POST",
                    path="/" + self.ticklist_reed_path,
                    handler=self._handle_ticklist_reed_post,
                )
            else:
                raise Exception(f"ApiFlowMeter actor does not recognize {self._component.cac.MakeModel}")
    
    def validate_config_params(self) -> None:
        if self._component.gt.HzCalcMethod == HzCalcMethod.BasicExpWeightedAvg:
            if self._component.gt.ExpAlpha is None:
                raise DcError(f"{self.name}: BasicExpWeightedAvg requires ExpAlpha")
        if self._component.gt.HzCalcMethod == HzCalcMethod.BasicButterWorth:
            if self._component.gt.CutoffFrequency is None:
                raise DcError(f"{self.name}: BasicButterWorth requiresCutoffFrequency")
        channel_names = [x.ChannelName for x in self._component.gt.ConfigList]
        if self.gpm_channel.Name not in channel_names:
            raise DcError(f"Missing {self.gpm_channel.Name} channel!")
        if self._component.gt.SendHz:
            if self.hz_channel.Name not in channel_names:
                raise DcError(f"SendHz but missing {self.hz_channel.Name}!")
        if self._component.gt.SendGallons:
            raise ValueError("Not set up to send gallons right now")

    @cached_property
    def hall_params_path(self) -> str:
        return f"{self.name}/flow-hall-params"
    
    @cached_property
    def ticklist_hall_path(self) -> str:
        return f"{self.name}/ticklist-hall"
    
    @cached_property
    def ticklist_reed_path(self) -> str:
        return f"{self.name}/ticklist-reed"
    
    @cached_property
    def reed_params_path(self) -> str:
        return f"{self.name}/flow-reed-params"
    
    def _send_to_scada(self, payload, qos: QOS = QOS.AtMostOnce): 
        if self.layout.parent_hierarchy_name(self.node.actor_hierarchy_name) == H0N.primary_scada:
            # If spawned by scada, use native proactor queue
            self._send(
                Message(
                    header=Header(Src=self.name,
                                  Dst=H0N.primary_scada,
                                  MessageType=payload.TypeName,
                            ),
                    Payload=payload
                )
            )
        else:
            # Otherwise send via local mqtt
            message = Message(Src=self.name, Payload=payload)
            return self.services._links.publish_message(self.services.LOCAL_MQTT, message, qos=qos)

    async def _get_text(self, request: Request) -> Optional[str]:
        try:
            return await request.text()
        except Exception as e:
            self.services.send_threadsafe(
                Message(
                    Payload=Problems(errors=[e]).problem_event(
                        summary=(
                            f"ERROR awaiting post ext <{self.name}>: {type(e)} <{e}>"
                        ),
                    )
                )
            )
        return None

    def _report_post_error(self, exception: BaseException, text: str) -> None:
        self.services.send_threadsafe(
            Message(
                Payload=Problems(
                    msg=f"request: <{text}>",
                    errors=[exception]
                ).problem_event(
                    summary=(
                        "Pico POST processing error for "
                        f"<{self._name}>: {type(exception)} <{exception}>"
                    ),
                )
            )
        )

    def need_to_update_layout(self) -> bool:
        if self._component.gt.PicoHwUid:
            return False
        return True

    async def _handle_reed_params_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.params_text = text
        try:
            params = FlowReedParams(**json.loads(text))
        except BaseException as e:
            self._report_post_error(e, "malformed FlowReed parameters!")
            return
        if params.ActorNodeName != self.name:
            return
        if (self._component.gt.PicoHwUid is None or 
            self._component.gt.PicoHwUid == params.HwUid):
            if self._component.gt.PicoHwUid is None:
                self.hw_uid = params.HwUid
                # TODO: update params from layout
                print(f"Layout update: {self.name} Pico HWUID {params.HwUid}")
                # TODO: send message to self so that writing to hardware layout isn't 
                # happening in IO loop
            return Response(text=params.model_dump_json())
        else:
            # A strange pico is identifying itself as our "a" tank
            print(f"unknown pico {params.HwUid} identifying as {self.name} Pico A!")
            # TODO: send problem report?
            return Response()

    async def _handle_hall_params_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.params_text = text
        try:
            params = FlowHallParams(**json.loads(text))
        except BaseException as e:
            self._report_post_error(e, "malformed FlowHall parameters!")
            return
        if params.ActorNodeName != self.name:
            return
        if (self._component.gt.PicoHwUid is None or 
            self._component.gt.PicoHwUid == params.HwUid):
            if self._component.gt.PicoHwUid is None:
                self.hw_uid = params.HwUid
                # TODO: update params from layout
                print(f"Layout update: {self.name} Pico HWUID {params.HwUid}")
                # TODO: send message to self so that writing to hardware layout isn't 
                # happening in IO loop
            return Response(text=params.model_dump_json())
        else:
            # A strange pico is identifying itself as our "a" tank
            print(f"unknown pico {params.HwUid} identifying as {self.name} Pico A!")
            # TODO: send problem report?
            return Response()
    
    async def _handle_reed_params_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.params_text = text
        try:
            params = FlowReedParams(**json.loads(text))
        except BaseException as e:
            self._report_post_error(e, "malformed tankmodule parameters!")
            return
        if params.ActorNodeName != self.name:
            return
        if (self._component.gt.PicoHwUid is None or 
            self._component.gt.PicoHwUid == params.HwUid):
            if self._component.gt.PicoHwUid is None:
                self.hw_uid = params.HwUid
                # TODO: update params from layout
                print(f"Layout update: {self.name} Pico HWUID {params.HwUid}")
                # TODO: send message to self so that writing to hardware layout isn't 
                # happening in IO loop
            return Response(text=params.model_dump_json())
        else:
            # A strange pico is identifying itself as our "a" tank
            print(f"unknown pico {params.HwUid} identifying as {self.name} Pico A!")
            # TODO: send problem report?
            return Response()
        
    async def _handle_ticklist_reed_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.readings_text = text
        if isinstance(text, str):
            try:
                self.services.send_threadsafe(
                    Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=TicklistReed(**json.loads(text))
                    )
                )
            except Exception as e: # noqa
                self._report_post_error(e, text)
        return Response()
                
    async def _handle_ticklist_hall_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.readings_text = text
        if isinstance(text, str):
            try:
                self.services.send_threadsafe(
                    Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=TicklistHall(**json.loads(text))
                    )
                )
            except Exception as e: # noqa
                self._report_post_error(e, text)
        return Response()  
    
    def update_timestamps_for_reed(self, data: TicklistReed) -> None:
        # Consider processing more than one batch at a time
        # if using filtering?
        pi_time_received_post = time.time_ns()
        pico_time_before_post = data.PicoBeforePostTimestampNanoSecond
        pico_time_delay_ns = pi_time_received_post - pico_time_before_post
        self.nano_timestamps = sorted(list(set([data.FirstTickTimestampNanoSecond 
                                         + pico_time_delay_ns 
                                         + x*1e6 for x in data.RelativeMillisecondList])))
    
    def update_timestamps_for_hall(self, data: TicklistHall) -> None:
        pi_time_received_post = time.time_ns()
        pico_time_before_post = data.PicoBeforePostTimestampNanoSecond
        pico_time_delay_ns = pi_time_received_post - pico_time_before_post
        self.nano_timestamps = sorted(list(set([data.FirstTickTimestampNanoSecond 
                                         + pico_time_delay_ns 
                                         + x*1e3 for x in data.RelativeMicrosecondList])))

    def publish_zero_flow(self):
        if self.latest_gpm * 10  > self._component.gt.AsyncCaptureThresholdGpmTimes10:
            channel_names = [self.gpm_channel.Name]
            values = [0]

            if self._component.gt.SendHz:
                channel_names.append(self.hz_channel.Name)
                values.append(0)

            self._send_to_scada(
                SyncedReadings(
                    ChannelNameList=channel_names,
                    ValueList=values,
                    ScadaReadTimeUnixMs=int(time.time() * 1000),
                )
            )

    def _process_ticklist_reed(self, data: TicklistReed) -> None:
        if data.HwUid != self.hw_uid:
            print(f"{self.name}: Ignoring data from pico {data.HwUid} - expect {self.hw_uid}!")
            return
        if len(data.RelativeMillisecondList) == 0:
            if self.latest_gpm is None:
                self.publish_zero_flow()
            elif self.latest_gpm * 10 > self._component.gt.AsyncCaptureThresholdGpmTimes10:
                self.publish_zero_flow()
        elif len(data.RelativeMillisecondList) == 1:
            raise ValueError("Shouldn't get a list of length 1 in TicklistReed!")
        else:
            if self._component.gt.SendTickLists:
                self._send_to_scada(TicklistReedReport(
                    TerminalAssetAlias=self.services.hardware_layout.terminal_asset_g_node_alias,
                    FlowNodeName=self._component.gt.FlowNodeName,
                    ScadaReceivedUnixMs=int(time.time() * 1000),
                    Ticklist=data
                ))
            self.update_timestamps_for_reed(data)
            hz_readings = self.get_hz_readings()
            if len(hz_readings) > 0:
                gpm_readings = self.get_gpm_readings(hz_readings)
                self._send_to_scada(gpm_readings)
                if self._component.gt.SendHz:
                    self._send_to_scada(hz_readings)
    
    def _process_ticklist_hall(self, data: TicklistHall) -> None:
        if data.HwUid != self.hw_uid:
            print(f"{self.name}: Ignoring data from pico {data.HwUid} - expect {self.hw_uid}!")
            return
        if len(data.RelativeMicrosecondList) <= 1:
            if self.latest_gpm is None:
                self.publish_zero_flow()
            elif self.latest_gpm * 10 > self._component.gt.AsyncCaptureThresholdGpmTimes10:
                self.publish_zero_flow()
        else:
            if self._component.gt.SendTickLists:
                self._send_to_scada(TicklistHallReport(
                    TerminalAssetAlias=self.services.hardware_layout.terminal_asset_g_node_alias,
                    FlowNodeName=self._component.gt.FlowNodeName,
                    ScadaReceivedUnixMs=int(time.time() * 1000),
                    Ticklist=data
                ))
            self.update_timestamps_for_hall(data)
            hz_readings = self.get_hz_readings()
            if len(hz_readings) > 0:
                gpm_readings = self.get_gpm_readings(hz_readings)
                self._send_to_scada(gpm_readings)
                if self._component.gt.SendHz:
                    self._send_to_scada(hz_readings)
        
    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case TicklistReed():
                self._process_ticklist_reed(message.Payload)
            case TicklistHall():
                self._process_ticklist_hall(message.Payload)
        return Ok(True)

    def start(self) -> None:
        """IOLoop will take care of start."""

    def stop(self) -> None:
        """IOLoop will take care of stop."""

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
    
    def get_gpm_readings(self, hz_readings: ChannelReadings) -> ChannelReadings:
        if self._component.gt.GpmFromHzMethod != GpmFromHzMethod.Constant:
            raise ValueError(f"Don't have method to handle GpmFromHzMethod {self._component.gt.GpmFromHzMethod}")
        if self.gpm_channel.TelemetryName != TelemetryName.FrequencyMicroHz.value:
            raise ValueError(f"Expected FrequencyMicroHz for {self.gpm_channel.Name}, got {self.gpm_channel.TelemetryName}")
        gallons_per_tick = self._component.gt.ConstantGallonsPerTick
        gpms = [x * 60 * gallons_per_tick for x in hz_readings.ValueList]
        return ChannelReadings(
            ChannelName=self.gpm_channel.Name,
            ValueList = [int(x * 1e6) for x in gpms],
            ScadaReadTimeUnixMsList=hz_readings.ScadaReadTimeUnixMsList
        )

    def get_hz_readings(self) -> ChannelReadings:
        if len(self.nano_timestamps) < 2:
            raise ValueError(f"Should only call get_hz_readings with at least 2 timestamps!")
        self.nano_timestamps = sorted(self.nano_timestamps) # Make sure timestamps are sorted
        frequencies = [1/(t2-t1)*1e9 for t1,t2 in zip(self.nano_timestamps[:-1], self.nano_timestamps[1:])]
        # Sort values by time
        # Remove outliers
        min_hz, max_hz = 0, 500
        self.nano_timestamps = [self.nano_timestamps[i] for i in range(len(frequencies)) if (frequencies[i]<max_hz and frequencies[i]>=min_hz)]
        frequencies = [x for x in frequencies  if (x<max_hz and x>=min_hz)]

        # Add 0 flow when there is more than no_flow_ms between two points
        new_timestamps = []
        new_frequencies = []
        for i in range(len(self.nano_timestamps) - 1):
            new_timestamps.append(self.nano_timestamps[i]) 
            new_frequencies.append(frequencies[i])  
            no_flow_ms = self._component.gt.NoFlowMs
            if self.nano_timestamps[i+1] - self.nano_timestamps[i] > no_flow_ms*1e6:
                add_step_ns = 0
                while self.nano_timestamps[i] + add_step_ns < self.nano_timestamps[i+1]:
                    add_step_ns += 10*1e6
                    new_timestamps.append(self.nano_timestamps[i] + add_step_ns)
                    new_frequencies.append(0.001)
        new_timestamps.append(self.nano_timestamps[-1])
        new_frequencies.append(frequencies[-1])
        sorted_times_values = sorted(zip(new_timestamps, new_frequencies))
        timestamps, frequencies = zip(*sorted_times_values)

        if self.latest_hz is None:
                self.latest_hz = frequencies[0]
        if self._component.gt.HzCalcMethod == HzCalcMethod.BasicExpWeightedAvg:
            smoothed_frequencies = [self.latest_hz] + [frequencies[0]]*len(frequencies)
            alpha = self._component.gt.ExpAlpha
            for t in range(len(frequencies)):
                smoothed_frequencies[t+1] = (1-alpha)*smoothed_frequencies[t] + alpha*frequencies[t+1]
            sampled_timestamps = list(timestamps)

        elif self._component.gt.HzCalcMethod == HzCalcMethod.BasicButterWorth:
            if len(frequencies) > 20:
                # Add the last recorded frequency before the filtering (avoids overfitting the first point)
                timestamps = [timestamps[0]-0.01*1e9] + list(timestamps)
                frequencies = [self.latest_hz] + list(frequencies)
                # Re-sample time at sampling frequency f_s
                f_s = 5 * max(frequencies)
                sampled_timestamps = np.linspace(min(timestamps), max(timestamps), int((max(timestamps)-min(timestamps))/1e9 * f_s))
                # Re-sample frequency accordingly using a linear interpolaton
                interpolation_function = interp1d(timestamps, frequencies)
                sampled_frequencies = interpolation_function(sampled_timestamps)
                # Butterworth low-pass filter
                cutoff_frequency=self._component.gt.CutoffFrequency
                b, a = butter(N=5, Wn=cutoff_frequency, fs=f_s, btype='low', analog=False)
                smoothed_frequencies = filtfilt(b, a, sampled_frequencies)
                # Remove points resulting from adding the first recorded frequency
                frequencies = frequencies[1:]
                timestamps = timestamps[1:]
                smoothed_frequencies = [smoothed_frequencies[i] for i in range(len(smoothed_frequencies)) 
                                        if sampled_timestamps[i]>=timestamps[1]]
                sampled_timestamps = [x for x in sampled_timestamps if x>=timestamps[1]]
            else:
                sampled_timestamps = timestamps
                smoothed_frequencies = frequencies
        if len(sampled_timestamps) != len(smoothed_frequencies):
            raise Exception("Sampled Timestamps and Smoothed Frequencies not the same length!")
        

        threshold_gpm = self._component.gt.AsyncCaptureThresholdGpmTimes10 / 10
        gallons_per_tick = self._component.gt.ConstantGallonsPerTick
        threshold_hz = threshold_gpm/60/gallons_per_tick

        micro_hz_list = []
        unix_ms_times = []
        # apply the async on change criterion:
        for i in range(len(smoothed_frequencies)):
            if abs(smoothed_frequencies[i] - self.latest_hz) > threshold_hz:
                micro_hz_list.append(int(smoothed_frequencies[i]*1e6))
                unix_ms_times.append(int(sampled_timestamps/1e6))
            self.latest_hz = smoothed_frequencies[i]

        return ChannelReadings(
            ChannelName=self.hz_channel.Name,
            ValueList=micro_hz_list,
            ScadaReadTimeUnixMsList=unix_ms_times,
        )

