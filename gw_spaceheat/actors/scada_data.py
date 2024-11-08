"""Container for data Scada uses in building status and snapshot messages, separated from Scada for clarity,
not necessarily re-use. """

import time
import uuid
from typing import Dict
from typing import List
from typing import Optional

from gwproto.messages import ChannelReadings
from gwproto.messages import Report
from gwproto.messages import SingleReading
from gwproto.messages import SnapshotSpaceheat

from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.data_channel import DataChannel

class ScadaData:
    latest_total_power_w: Optional[int]
    reports_to_store: Dict[str, Report]
    latest_channel_unix_ms: Dict[DataChannel, int]
    latest_channel_values: Dict[DataChannel, int]
    recent_channel_values: Dict[DataChannel, List]
    recent_channel_unix_ms: Dict[DataChannel, List]
    settings: ScadaSettings
    hardware_layout: HardwareLayout

    def __init__(self, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.latest_total_power_w: Optional[int] = None
        self.latest_total_power_w: Optional[int] = None
        self.reports_to_store: Dict[str:Report] = {}
        self.seconds_by_channel: Dict[str:int] = {}

        self.settings = settings
        self.hardware_layout = hardware_layout
        self.my_channels = self.get_my_channels()

        self.latest_channel_values: Dict[DataChannel, int] = {  # noqa
            ch: None for ch in self.my_channels
        }
        self.latest_channel_unix_ms: Dict[DataChannel, int] = {  # noqa
            ch: None for ch in self.my_channels
        }
        self.recent_channel_values: Dict[DataChannel, List] = {
            ch: [] for ch in self.my_channels
        }
        self.recent_channel_unix_ms: Dict[
            DataChannel, List
        ] = {ch: [] for ch in self.my_channels}

        self.flush_latest_readings()
    
    def get_my_channels(self) -> List[DataChannel]:
        return list(self.hardware_layout.data_channels.values())

    def flush_latest_readings(self):
        self.recent_channel_values = {
            ch: [] for ch in self.my_channels
        }
        self.recent_channel_unix_ms = {
            ch: [] for ch in self.my_channels
        }

    def make_channel_readings(
        self, ch: DataChannel
    ) -> Optional[ChannelReadings]:
        if ch in self.my_channels:
            if len(self.recent_channel_values[ch]) == 0:
                return None
            return ChannelReadings(
                ChannelName=ch.Name,
                ChannelId=ch.Id,
                ValueList=self.recent_channel_values[ch],
                ScadaReadTimeUnixMsList=self.recent_channel_unix_ms[ch],
            )
        else:
            return None

    def make_report(self, slot_start_seconds: int) -> Report:
        channel_reading_list = []
        for ch in self.my_channels:
            channel_readings = self.make_channel_readings(ch)
            if  channel_readings:
                channel_reading_list.append(channel_readings)
        return Report(
            FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
            FromGNodeInstanceId=self.hardware_layout.scada_g_node_id,
            AboutGNodeAlias=self.hardware_layout.terminal_asset_g_node_alias,
            SlotStartUnixS=slot_start_seconds,
            SlotDurationS=self.settings.seconds_per_report,
            ChannelReadingList=channel_reading_list,
            FsmActionList=[],
            FsmReportList=[],
            MessageCreatedMs=int(time.time() * 1000),
            Id=str(uuid.uuid4())
        )

    def capture_seconds(self, ch: DataChannel) -> int: 
        if ch.Name not in self.seconds_by_channel:
            self.seconds_by_channel == {}
            components = [c.gt for c in self.hardware_layout.components.values()]
            for c in components:
                for config in c.ConfigList:
                    self.seconds_by_channel[config.ChannelName] = config.CapturePeriodS 
        return self.seconds_by_channel[ch.Name]

    def flatlined(self, ch: DataChannel) -> bool:
        if self.latest_channel_unix_ms[ch] is None:
            return True
        # nyquist
        nyquist = 2.1 # https://en.wikipedia.org/wiki/Nyquist_frequency
        if time.time() - (self.latest_channel_unix_ms[ch] / 1000) > self.capture_seconds(ch) * nyquist:
            return True
        return False

    def make_snapshot(self) -> SnapshotSpaceheat:
        latest_reading_list = []
        for ch in self.my_channels:
            if not self.flatlined(ch):
                latest_reading_list.append(
                    SingleReading(
                        ChannelName=ch.Name,
                        Value=self.latest_channel_values[ch],
                        ScadaReadTimeUnixMs=self.latest_channel_unix_ms[ch]
                    )
                )
        return SnapshotSpaceheat(
            FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
            FromGNodeInstanceId=self.hardware_layout.scada_g_node_id,
            SnapshotTimeUnixMs=int(time.time() * 1000),
            LatestReadingList=latest_reading_list,
        )
