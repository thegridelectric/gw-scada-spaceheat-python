"""Proactor-internal messages wrappers of Scada message structures."""

import time
from typing import List
from typing import cast

from gwproto.enums import TelemetryName
from gwproto.message import Header
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import GtShTelemetryFromMultipurposeSensor


class PowerWattsMessage(Message[PowerWatts]):
    def __init__(
        self,
        src: str,
        dst: str,
        power: int,
    ):
        payload = cast(PowerWatts, PowerWatts(Watts=power))
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


class MultipurposeSensorTelemetryMessage(Message[GtShTelemetryFromMultipurposeSensor]):
    def __init__(
        self,
        src: str,
        dst: str,
        about_node_name_list: List[str],
        value_list: List[int],
        telemetry_name_list: List[TelemetryName],
    ):
        payload = GtShTelemetryFromMultipurposeSensor(
            AboutNodeAliasList=about_node_name_list,
            ValueList=value_list,
            TelemetryNameList=telemetry_name_list,
            ScadaReadTimeUnixMs=int(1000 * time.time()),
        )
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


