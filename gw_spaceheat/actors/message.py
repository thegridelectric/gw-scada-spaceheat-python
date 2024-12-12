"""Proactor-internal messages wrappers of Scada message structures."""

import time
from typing import List
from typing import cast
from typing import Literal

from gwproto.enums import TelemetryName
from gwproto.message import Header
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import SyncedReadings
from pydantic import BaseModel


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


class SyncedReadingsMessage(Message[SyncedReadings]):
    def __init__(
        self,
        src: str,
        dst: str,
        channel_name_list: List[str],
        value_list: List[int],
    ):
        payload = SyncedReadings(
            ChannelNameList=channel_name_list,
            ValueList=value_list,
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