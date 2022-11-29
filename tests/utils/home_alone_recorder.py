from typing import Optional

from actors.home_alone import HomeAlone
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto.messages import GtShStatus


class HomeAloneRecorder(HomeAlone):
    status_received: int
    latest_status_payload: Optional[GtShStatus]

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.status_received = 0
        self.latest_status_payload: Optional[GtShStatus] = None
        super().__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShStatus):
            self.status_received += 1
            self.latest_status_payload = payload
        super().on_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        return (
            f"HomeAloneRecorder [{self.node.alias}] status_received: {self.status_received}  "
            f"latest_status_payload: {self.latest_status_payload}"
        )
