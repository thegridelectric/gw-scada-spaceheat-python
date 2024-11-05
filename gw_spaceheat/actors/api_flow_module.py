import json
import time
import asyncio
from gwproactor.message import InternalShutdownMessage
from functools import cached_property
from typing import List, Literal, Optional
from gw.errors import DcError
import numpy as np
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from gwproactor import Actor, ServicesInterface, Problems
from gwproto import Message
from gwproto.messages import ProblemEvent
from gwproto.message import Header
from gwproto.data_classes.components import PicoFlowModuleComponent
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import MakeModel, HzCalcMethod, GpmFromHzMethod, TelemetryName
from gwproto.named_types import  ChannelReadings, SyncedReadings
from gwproto.named_types import TicklistHall, TicklistReed, TicklistHallReport, TicklistReedReport
from gwproto.named_types.web_server_gt import DEFAULT_WEB_SERVER_NAME
from pydantic import BaseModel
from gwproactor import QOS
from result import Ok, Result
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt

FLATLINE_REPORT_S = 60

class FlowHallParams(BaseModel):
    HwUid: str
    ActorNodeName: str
    FlowNodeName: str
    PublishTicklistPeriodS: int
    PublishEmptyTicklistAfterS: int
    TypeName: Literal["flow.hall.params"] = "flow.hall.params"
    Version: Literal["101"] = "101"

class FlowReedParams(BaseModel):
    HwUid: str
    ActorNodeName: str
    FlowNodeName: str
    PublishTicklistLength: int
    PublishAnyTicklistAfterS: int
    DeadbandMilliseconds: int
    TypeName: Literal["flow.reed.params"] = "flow.reed.params"
    Version: Literal["101"] = "101"


class ApiFlowModule(Actor):
    _stop_requested: bool
    _component: PicoFlowModuleComponent
    last_heard: float
    latest_gpm: float
    latest_hz: float
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
        self._stop_requested: bool = False
        self.layout = self.services.hardware_layout
        self._component = component
        self.hw_uid = self._component.gt.HwUid
        self.nano_timestamps: List[int] = [] # nanoseconds
        self.latest_tick_ns = None
        self.latest_report_ns = None
        self.latest_hz = None
        self.latest_gpm = None
        self.latest_gallons = 0
        self.gpm_channel = self.layout.data_channels[f"{self.name}"]
        self.hz_channel = self.layout.data_channels[f"{self.name}-hz"]
        self.capture_s = self._component.gt.ConfigList[0].CapturePeriodS
        self.latest_sync_send_s = time.time()
        self.last_heard = time.time()
        self.last_error_report = time.time()
        self.validate_config_params()
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
                raise DcError(f"{self.name}: BasicButterWorth requires CutoffFrequency")
        channel_names = [x.ChannelName for x in self._component.gt.ConfigList]
        if self.gpm_channel.Name not in channel_names:
            raise DcError(f"Missing {self.gpm_channel.Name} channel!")
        if self._component.gt.SendHz:
            if self.hz_channel.Name not in channel_names:
                raise DcError(f"SendHz but missing {self.hz_channel.Name}!")
        if self._component.gt.SendGallons:
            raise ValueError("Not set up to send gallons right now")

    @property
    def last_sync_s(self) -> int:
        last_sync_s = self.latest_sync_send_s - ((self.latest_sync_send_s + 1) % self.capture_s)
        return int(last_sync_s)

    @property
    def next_sync_s(self) -> int:
        return self.last_sync_s + self.capture_s

    def sync_reading_sleep(self) -> int:
        if self.capture_s <= 3:
            return 1
        if (time.time() - self.last_sync_s) < 2:
            return self.capture_s - 2.2
        else:
            return 1

    def publish_synced_readings(self):
        if self.latest_gpm is not None:
            channel_names = [self.gpm_channel.Name]
            values = [int(self.latest_gpm * 100)]
            if self._component.gt.SendHz:
                channel_names.append(self.hz_channel.Name)
                values.append(int(1e6 * self.latest_hz))
            self._send_to_scada(
                SyncedReadings(
                    ChannelNameList=channel_names,
                    ValueList=values,
                    ScadaReadTimeUnixMs=int(time.time() * 1000)
                )
            )

    def flatline_seconds(self) -> int:
        if self._component.cac.MakeModel == MakeModel.GRIDWORKS__PICOFLOWHALL:
            return self._component.gt.PublishEmptyTicklistAfterS * 2.5
        if self._component.cac.MakeModel == MakeModel.GRIDWORKS__PICOFLOWREED:
            return self._component.gt.PublishAnyTicklistAfterS * 2.5
    
    async def main(self):
        while not self._stop_requested:
            # check if flatlined, if so send a complaint every minute
            if (time.time() - self.last_heard > self.flatline_seconds()) and \
               (time.time() -self.last_error_report > FLATLINE_REPORT_S):
                self.latest_gpm = None
                self.latest_hz = None
                self._send(
                    Message(
                        Src=self.name,
                        Dst=H0N.primary_scada,
                        Payload=Problems(warnings=["Pico down"]).problem_event(summary=self.name)
                    )
                )
                self.last_error_report = time.time()
            # publish readings synchronously every capture_s
            try:
                if time.time() > self.next_sync_s:    
                    self.publish_synced_readings()
                    self.latest_sync_send_s = int(time.time())
                await asyncio.sleep(self.sync_reading_sleep())
            except Exception as e:
                try:
                    if not isinstance(e, asyncio.CancelledError):
                        self.services.logger.exception(e)
                        self._send(
                            InternalShutdownMessage(
                                Src=self.name,
                                Reason=(
                                    f"update_flow_sync_readings() task got exception: <{type(e)}> {e}"
                                ),
                            )
                        )
                finally:
                    break

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
                    Payload=ProblemEvent(errors=[e]).problem_event(
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
        if self._component.gt.HwUid:
            return False
        return True

    async def _handle_hall_params_post(self, request: Request) -> Response:
        text = await self._get_text(request)
        self.params_text = text
        try:
            params = FlowHallParams(**json.loads(text))
        except BaseException as e:
            self._report_post_error(e, "malformed FlowHall parameters!")
            return
        if params.FlowNodeName != self._component.gt.FlowNodeName:
            return
        if self._component.cac.MakeModel != MakeModel.GRIDWORKS__PICOFLOWHALL:
            raise Exception(f"{self.name} has {self._component.cac.MakeModel}"
                            "but got FlowHallParams!")
        print(f"\nGot params for {params.HwUid}:\n{params}")
        # temporary hack prior to installerapp - in case a pico gets installed
        # and the hardware layout does not have its id yet
        if (self._component.gt.HwUid is None or 
            self._component.gt.HwUid == params.HwUid):
            if self._component.gt.HwUid is None:
                self.hw_uid = params.HwUid
                # TODO: update params from layout
                # print(f"Layout update: {self.name} Pico HWUID {params.HwUid}")
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
        if params.FlowNodeName != self._component.gt.FlowNodeName:
            return
        if self._component.cac.MakeModel != MakeModel.GRIDWORKS__PICOFLOWREED:
            raise Exception(f"{self.name} has {self._component.cac.MakeModel}"
                            "but got FlowReedParams!")
        print(f"\nGot params for {params.HwUid}:\n{params}")
        if (self._component.gt.HwUid is None or 
            self._component.gt.HwUid == params.HwUid):
            if self._component.gt.HwUid is None:
                self.hw_uid = params.HwUid
                # TODO: update params from layout
                print(f"Layout update: {self.name} Pico HWUID {params.HwUid}")
                # TODO: send message to self so that writing to hardware layout isn't 
                # happening in IO loop
            new_params = FlowReedParams(
                HwUid=params.HwUid,
                ActorNodeName=self.name,
                FlowNodeName=params.FlowNodeName,
                PublishTicklistLength=params.PublishTicklistLength,
                PublishAnyTicklistAfterS=self._component.gt.PublishAnyTicklistAfterS,
                DeadbandMilliseconds=params.DeadbandMilliseconds,
            )
            print(f"returning {new_params}")
            return Response(text=new_params.model_dump_json())
        else:
            # A strange pico is identifying itself as our "a" tank
            print(f"unknown pico {params.HwUid} identifying as {self.name} Pico A!")
            # TODO: send problem report?
            return Response()
        
    async def _handle_ticklist_reed_post(self, request: Request) -> Response:
        if self._component.cac.MakeModel != MakeModel.GRIDWORKS__PICOFLOWREED:
            raise Exception(f"{self.name} has {self._component.cac.MakeModel}"
                            "but got TicklistReed!")
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
        if self._component.cac.MakeModel != MakeModel.GRIDWORKS__PICOFLOWHALL:
            raise Exception(f"{self.name} has {self._component.cac.MakeModel}"
                            "but got TicklistHall!")
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
        channel_names = [self.gpm_channel.Name]
        values = [0]
        # if there weren't any ticks, then we want to set the flow
        # to be zero very shortly after the LAST tick we got (unless
        # this is the first message we've ever gotten
        zero_flow_ms = int(time.time() * 1000)
        if self.latest_report_ns:
            if self.latest_tick_ns == self.latest_report_ns:
                self.latest_report_ns = self.latest_tick_ns + 1e8 # 100 ms AFTER last tick
                zero_flow_ms = int(self.latest_report_ns / 1e6)
        if self._component.gt.SendHz:
            channel_names.append(self.hz_channel.Name)
            values.append(0)

        self._send_to_scada(
            SyncedReadings(
                ChannelNameList=channel_names,
                ValueList=values,
                ScadaReadTimeUnixMs=zero_flow_ms,
            )
        )

    def _process_ticklist_reed(self, data: TicklistReed) -> None:
        self.ticklist = data
        if data.HwUid != self.hw_uid:
            print(f"{self.name}: Ignoring data from pico {data.HwUid} - expect {self.hw_uid}!")
            return
        self.last_heard = time.time()
        if len(data.RelativeMillisecondList) == 0:
            if self.latest_gpm is None:
                self.latest_gpm = 0
                self.latest_hz = 0
                self.publish_zero_flow()
            elif self.latest_gpm * 100 > self._component.gt.AsyncCaptureThresholdGpmTimes100:
                self.publish_zero_flow()
                self.latest_gpm = 0
                self.latest_hz = 0
            return
        # now we can assume we have at least one tick
        self.update_timestamps_for_reed(data)
        if self._component.gt.SendTickLists:
                self._send_to_scada(TicklistReedReport(
                    TerminalAssetAlias=self.services.hardware_layout.terminal_asset_g_node_alias,
                    FlowNodeName=self._component.gt.FlowNodeName,
                    ScadaReceivedUnixMs=int(time.time() * 1000),
                    Ticklist=data
                ))
        if len(data.RelativeMillisecondList) == 1:
            final_tick_ns = self.nano_timestamps[-1]
            if self.latest_tick_ns is not None:
                final_nonzero_hz = int(1e9/(final_tick_ns - self.latest_tick_ns))
            else:
                final_nonzero_hz = 0
            self.latest_tick_ns = final_tick_ns
            self.latest_report_ns = final_tick_ns
            self.latest_hz = 0
            micro_hz_readings = ChannelReadings(
                ChannelName=self.hz_channel.Name,
                ValueList=[int(final_nonzero_hz * 1e6), 0],
                ScadaReadTimeUnixMsList=[int(final_tick_ns/1e6), int(final_tick_ns/1e6) + 10]
            )
        else:
            micro_hz_readings = self.get_micro_hz_readings()
            
        if len(micro_hz_readings.ValueList) > 0:
            gpm_readings = self.get_gpm_readings(micro_hz_readings)
            self.gpm_readings = gpm_readings
            self._send_to_scada(gpm_readings)
            self.latest_sync_send_s = time.time()
            if self._component.gt.SendHz:
                self._send_to_scada(micro_hz_readings)
        

    def _process_ticklist_hall(self, data: TicklistHall) -> None:
        if data.HwUid != self.hw_uid:
            print(f"{self.name}: Ignoring data from pico {data.HwUid} - expect {self.hw_uid}!")
            return
        self.last_heard = time.time()
        if len(data.RelativeMicrosecondList) == 0:
            if self.latest_gpm is None:
                self.latest_gpm = 0
                self.latest_hz = 0
                self.publish_zero_flow()
            elif self.latest_gpm * 100 > self._component.gt.AsyncCaptureThresholdGpmTimes100:
                self.publish_zero_flow()
                self.latest_gpm = 0
                self.latest_hz = 0
            return
        if len(data.RelativeMicrosecondList) <= 1:
            if self.latest_gpm is None:
                self.publish_zero_flow()
            elif self.latest_gpm * 100 > self._component.gt.AsyncCaptureThresholdGpmTimes100:
                self.publish_zero_flow()
        else:
            if self._component.gt.SendTickLists:
                self._send_to_scada(TicklistHallReport(
                    TerminalAssetAlias=self.services.hardware_layout.terminal_asset_g_node_alias,
                    FlowNodeName=self._component.gt.FlowNodeName,
                    ScadaReceivedUnixMs=int(time.time() * 1000),
                    Ticklist=data
                ))
            self.ticklist = data
            self.update_timestamps_for_hall(data)
            if len(data.RelativeMicrosecondList) > 0:
                hz_readings = self.get_micro_hz_readings()
                if len(hz_readings.ValueList) > 0:
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
        self.services.add_task(
            asyncio.create_task(self.main(), name="update_flow_sync_readings")
        )

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
    
    def get_gpm_readings(self, micro_hz_readings: ChannelReadings) -> ChannelReadings:
        if self._component.gt.GpmFromHzMethod != GpmFromHzMethod.Constant:
            raise ValueError(f"Don't have method to handle GpmFromHzMethod {self._component.gt.GpmFromHzMethod}")
        if self.gpm_channel.TelemetryName != TelemetryName.GpmTimes100.value:
            raise ValueError(f"Expectedfor GomTimes100 for {self.gpm_channel.Name}, got {self.gpm_channel.TelemetryName}")
        gallons_per_tick = self._component.gt.ConstantGallonsPerTick
        hz_list = [x / 1e6 for x in micro_hz_readings.ValueList]
        gpms = [x * 60 * gallons_per_tick for x in hz_list]
        self.latest_gpm = gpms[-1]
        return ChannelReadings(
            ChannelName=self.gpm_channel.Name,
            ValueList = [int(x * 100) for x in gpms],
            ScadaReadTimeUnixMsList=micro_hz_readings.ScadaReadTimeUnixMsList
        )

    def get_micro_hz_readings(self) -> ChannelReadings:
        if len(self.nano_timestamps) < 2:
            raise ValueError(f"Should only call get_hz_readings with at least 2 timestamps!")
        first_reading = False
        # Sort timestamps and compute frequencies
        self.nano_timestamps = sorted(self.nano_timestamps)
        frequencies = [1/(t2-t1)*1e9 for t1,t2 in zip(self.nano_timestamps[:-1], self.nano_timestamps[1:])]
        # Remove outliers
        min_hz, max_hz = 0, 500 # TODO: make these parameters? Or enforce on the Pico (if not already done)
        self.nano_timestamps = [self.nano_timestamps[i] 
                                for i in range(len(frequencies)) 
                                if (frequencies[i]<max_hz and frequencies[i]>=min_hz)]
        frequencies = [x for x in frequencies  if (x<max_hz and x>=min_hz)]
        # Add 0 flow when there is more than no_flow_ms between two points
        new_timestamps = []
        new_frequencies = []
        no_flow_ms = self._component.gt.NoFlowMs
        for i in range(len(self.nano_timestamps) - 1):
            new_timestamps.append(self.nano_timestamps[i]) 
            new_frequencies.append(frequencies[i])  
            if self.nano_timestamps[i+1] - self.nano_timestamps[i] > no_flow_ms*1e6:
                add_step_ns = 0
                while self.nano_timestamps[i] + add_step_ns < self.nano_timestamps[i+1]:
                    add_step_ns += 10*1e6
                    new_timestamps.append(self.nano_timestamps[i] + add_step_ns)
                    new_frequencies.append(0.001)
        new_timestamps.append(self.nano_timestamps[-1])
        new_frequencies.append(frequencies[-1])
        timestamps = list(new_timestamps)
        frequencies = list(new_frequencies)
        del new_timestamps, new_frequencies
        # First reading
        if self.latest_hz is None:
            self.latest_hz = frequencies[0]
            first_reading = True
        # Exponential weighted average
        if self._component.gt.HzCalcMethod == HzCalcMethod.BasicExpWeightedAvg:
            alpha = self._component.gt.ExpAlpha
            smoothed_frequencies = []
            latest = self.latest_hz
            for t in range(len(frequencies)):
                latest = (1-alpha)*latest + alpha*frequencies[t]
                smoothed_frequencies.append(latest)
            sampled_timestamps = timestamps
        # Butterworth filter
        elif self._component.gt.HzCalcMethod == HzCalcMethod.BasicButterWorth:
            if len(frequencies) > 20: #TODO: make this a parameter? Issue a warning if too short?
                # Add the last recorded frequency before the filtering (avoids overfitting the first point)
                timestamps = [timestamps[0]-0.01*1e9] + list(timestamps)
                frequencies = [self.latest_hz] + list(frequencies)
                # Re-sample time at sampling frequency f_s
                f_s = 5 * max(frequencies)
                sampled_timestamps = np.linspace(min(timestamps), 
                                                 max(timestamps), 
                                                 int((max(timestamps)-min(timestamps))/1e9 * f_s))
                # Re-sample frequency accordingly using a linear interpolaton
                interpolation_function = interp1d(timestamps, frequencies)
                sampled_frequencies = interpolation_function(sampled_timestamps)
                # Butterworth low-pass filter on the re-sampled data
                cutoff_frequency=self._component.gt.CutoffFrequency
                b, a = butter(N=5, Wn=cutoff_frequency, fs=f_s, btype='low', analog=False)
                smoothed_frequencies = filtfilt(b, a, sampled_frequencies)
                # Remove points resulting from adding the first recorded frequency
                frequencies = frequencies[1:]
                timestamps = timestamps[1:]
                smoothed_frequencies = [smoothed_frequencies[i] 
                                        for i in range(len(smoothed_frequencies)) 
                                        if sampled_timestamps[i]>=timestamps[1]]
                sampled_timestamps = [x for x in sampled_timestamps if x>=timestamps[1]]
            else:
                print(f"Warning: ticklist was too short ({len(frequencies)} instead of 20), so no filtering applied.")
                sampled_timestamps = timestamps
                smoothed_frequencies = frequencies
        if len(sampled_timestamps) != len(smoothed_frequencies):
            raise Exception("Sampled Timestamps and Smoothed Frequencies not the same length!")
        # Convert GPM threshold to Hz threshold
        threshold_gpm = self._component.gt.AsyncCaptureThresholdGpmTimes100 / 100
        gallons_per_tick = self._component.gt.ConstantGallonsPerTick
        threshold_hz = threshold_gpm/60/gallons_per_tick
        # For the first reading
        if first_reading:
            self.latest_hz = int(smoothed_frequencies[0]*1e6) #TODO: check with Jessica
            micro_hz_list = [int(smoothed_frequencies[0]*1e6)]
            unix_ms_times = [int(sampled_timestamps[0]/1e6)]
        # Record Hz on change
        else:
            micro_hz_list = []
            unix_ms_times = []
        for i in range(len(smoothed_frequencies)):
            if abs(smoothed_frequencies[i] - self.latest_hz) > threshold_hz:
                micro_hz_list.append(int(smoothed_frequencies[i]*1e6))
                unix_ms_times.append(int(sampled_timestamps[i]/1e6))
        self.latest_hz = smoothed_frequencies[-1]
        self.latest_tick_ns = sampled_timestamps[-1]
        self.latest_report_ns = sampled_timestamps[-1]
        
        return ChannelReadings(
            ChannelName=self.hz_channel.Name,
            ValueList=micro_hz_list,
            ScadaReadTimeUnixMsList=unix_ms_times,
        )

