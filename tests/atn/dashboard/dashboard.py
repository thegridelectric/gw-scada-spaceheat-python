import logging
import time

from typing import Optional

from gwproto.data_classes.data_channel import DataChannel
from gwproto.types import PowerWatts
from gwproto.types import SnapshotSpaceheat

from tests.atn.atn_config import DashboardSettings
from tests.atn.dashboard.channels import Channels
from tests.atn.dashboard.display import Displays
from tests.atn.dashboard.hackhp import HackHp

class Dashboard:
    short_name: str
    settings: DashboardSettings
    data_channels: dict[str, DataChannel]
    hack_hp: HackHp
    channels: Channels
    displays: Displays
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    logger: logging.Logger | logging.LoggerAdapter

    def __init__(self,
        settings: DashboardSettings,
        atn_g_node_alias: str,
        data_channels: dict[str, DataChannel],
        logger = Optional[logging.Logger | logging.LoggerAdapter]
    ):
        self.settings = settings
        self.short_name = atn_g_node_alias.split(".")[-1]
        self.data_channels = data_channels
        if logger is None:
            logger = logging.getLogger(__file__)
        self.logger = logger
        self.hack_hp = HackHp(
            short_name=self.short_name,
            settings=self.settings.hack_hp,
            raise_dashboard_exceptions=self.settings.raise_dashboard_exceptions,
            logger=self.logger
        )
        self.channels = Channels(channels=self.data_channels)
        self.displays = Displays(self.channels)

    def process_snapshot(self, snapshot: SnapshotSpaceheat):
        self.latest_snapshot = snapshot
        self.channels.read_snapshot(self.latest_snapshot, self.data_channels)
        self.hack_hp.update_pwr(
            fastpath_pwr_w=None,
            channels=self.channels,
            report_time_s=int(snapshot.SnapshotTimeUnixMs / 1000),
        )
        self.refresh_gui()

    def process_power(self, power: PowerWatts) -> None:
        self.channels.read_snapshot(self.latest_snapshot, self.data_channels)
        self.hack_hp.update_pwr(
            fastpath_pwr_w=power.Watts,
            channels=self.channels,
            report_time_s=int(time.time())
        )
        self.refresh_gui()

    def refresh_gui(self) -> None:
        if self.latest_snapshot is None:
            return
        try:
            ...
        except Exception as e:
            self.logger.error("ERROR in refresh_gui")
            self.logger.exception(e)
            if self.settings.raise_dashboard_exceptions:
                raise
