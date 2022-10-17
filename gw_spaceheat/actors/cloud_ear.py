from typing import List

from actors.cloud_base import CloudBase
from actors.utils import QOS
from actors.utils import Subscription
from actors.utils import responsive_sleep
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto.messages import  GsPwr_Maker
from gwproto.messages import  GtDispatchBoolean_Maker
from gwproto.messages import  GtShStatus_Maker
from gwproto.messages import  SnapshotSpaceheat_Maker


class CloudEar(CloudBase):
    def __init__(self, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super(CloudEar, self).__init__(settings=settings, hardware_layout=hardware_layout)

        self.screen_print(f"Initialized {self.__class__}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GsPwr_Maker.type_alias}", Qos=QOS.AtMostOnce
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GtShStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{SnapshotSpaceheat_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, from_node: ShNode, payload):
        pass

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            responsive_sleep(self, 10)

    def screen_print(self, note):
        header = "Cloud Ear: "
        print(header + note)
