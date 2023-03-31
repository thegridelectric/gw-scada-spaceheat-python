"""Proactor-internal messages wrappers of Scada message structures."""

import time
from typing import List
from typing import cast

from gwproto.enums import TelemetryName
from gwproto.message import Header
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import PowerWatts_Maker
from gwproto.messages import GtDispatchBooleanLocal
from gwproto.messages import GtDispatchBooleanLocal_Maker
from gwproto.messages import GtDriverBooleanactuatorCmd
from gwproto.messages import GtDriverBooleanactuatorCmd_Maker
from gwproto.messages import GtShTelemetryFromMultipurposeSensor
from gwproto.messages import GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import GtTelemetry
from gwproto.messages import GtTelemetry_Maker

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
        payload = GtTelemetry_Maker(
            name=telemetry_name,
            value=value,
            exponent=exponent,
            scada_read_time_unix_ms=scada_read_time_unix_ms,
        ).tuple
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


class GtDriverBooleanactuatorCmdResponse(Message[GtDriverBooleanactuatorCmd]):
    def __init__(
        self,
        src: str,
        dst: str,
        relay_state: int,
    ):
        payload = GtDriverBooleanactuatorCmd_Maker(
            relay_state=relay_state,
            command_time_unix_ms=int(time.time() * 1000),
            sh_node_alias=src,
        ).tuple
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


class GtDispatchBooleanLocalMessage(Message[GtDispatchBooleanLocal]):
    def __init__(
        self,
        src: str,
        dst: str,
        relay_state: int,
    ):
        payload = GtDispatchBooleanLocal_Maker(
            from_node_name=src,
            about_node_name=dst,
            relay_state=relay_state,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
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
        payload = cast(PowerWatts, PowerWatts_Maker(watts=power).tuple)
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
        payload = GtShTelemetryFromMultipurposeSensor_Maker(
            about_node_alias_list=about_node_alias_list,
            value_list=value_list,
            telemetry_name_list=telemetry_name_list,
            scada_read_time_unix_ms=int(1000 * time.time()),
        ).tuple
        super().__init__(
            Header=Header(
                Src=src,
                Dst=dst,
                MessageType=payload.TypeName,
            ),
            Payload=payload,
        )


