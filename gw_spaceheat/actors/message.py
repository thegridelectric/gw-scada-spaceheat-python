"""Proactor-internal messages wrappers of Scada message structures."""

import time
from typing import List
from typing import cast

from gwproto.enums import TelemetryName
from gwproto.message import Header
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import GtDispatchBooleanLocal
from gwproto.messages import GtDriverBooleanactuatorCmd
from gwproto.messages import GtShTelemetryFromMultipurposeSensor
from gwproto.messages import GtTelemetry

class GtTelemetryMessage(Message[GtTelemetry]):
    def __init__(
        self,
        src: str,
        dst: str,
        telemetry_name: TelemetryName,
        value: int,
        exponent: int,
        scada_read_time_unix_ms: int,
    ):
        super().__init__(
            Src=src,
            Dst=dst,
            Payload=GtTelemetry(
                Name=telemetry_name,
                Value=value,
                Exponent=exponent,
                ScadaReadTimeUnixMs=scada_read_time_unix_ms,
            ),
        )


class GtDriverBooleanactuatorCmdResponse(Message[GtDriverBooleanactuatorCmd]):
    def __init__(
        self,
        src: str,
        dst: str,
        relay_state: bool,
    ):
        super().__init__(
            Src=src,
            Dst=dst,
            Payload=GtDriverBooleanactuatorCmd(
                RelayState=relay_state,
                CommandTimeUnixMs=int(time.time() * 1000),
                ShNodeAlias=src
            ),
        )


class GtDispatchBooleanLocalMessage(Message[GtDispatchBooleanLocal]):
    def __init__(
        self,
        src: str,
        dst: str,
        relay_state: bool,
    ):
        payload = GtDispatchBooleanLocal(
            FromNodeName=src,
            AboutNodeName=dst,
            RelayState=relay_state,
            SendTimeUnixMs=int(time.time() * 1000),
        )
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


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
        about_node_alias_list: List[str],
        value_list: List[int],
        telemetry_name_list: List[TelemetryName],
    ):
        payload = GtShTelemetryFromMultipurposeSensor(
            AboutNodeAliasList=about_node_alias_list,
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


