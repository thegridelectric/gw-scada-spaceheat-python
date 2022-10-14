"""Proactor-internal messages wrappers of Scada message structures."""

import time
from typing import (
    List,
    Optional,
    Literal,
    cast
)
from enum import Enum

from pydantic import BaseModel, validator

from logging_config import LoggerLevels
from proactor.message import Message, Header, as_enum
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from schema.gs.gs_pwr import GsPwr
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import (
    GtDispatchBooleanLocal,
)
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local_maker import (
    GtDispatchBooleanLocal_Maker,
)
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd import (
    GtDriverBooleanactuatorCmd,
)
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker import (
    GtDriverBooleanactuatorCmd_Maker,
)
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor import (
    GtShTelemetryFromMultipurposeSensor,
)
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker


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
            header=Header(
                src=src,
                dst=dst,
                message_type=payload.TypeAlias,
            ),
            payload=payload,
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
            header=Header(
                src=src,
                dst=dst,
                message_type=payload.TypeAlias,
            ),
            payload=payload,
        )


class GtDispatchBooleanLocalMessage(Message[GtDispatchBooleanLocal]):
    def __init__(
        self,
        src: str,
        dst: str,
        relay_state: int,
    ):
        payload = GtDispatchBooleanLocal_Maker(
            from_node_alias=src,
            about_node_alias=dst,
            relay_state=relay_state,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
        super().__init__(
            header=Header(
                src=src,
                dst=dst,
                message_type=payload.TypeAlias,
            ),
            payload=payload,
        )


class GsPwrMessage(Message[GsPwr]):
    def __init__(
        self,
        src: str,
        dst: str,
        power: int,
    ):
        payload = cast(GsPwr, GsPwr_Maker(power=power).tuple)
        super().__init__(
            header=Header(
                src=src,
                dst=dst,
                message_type=payload.TypeAlias,
            ),
            payload=payload,
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
            header=Header(
                src=src,
                dst=dst,
                message_type=payload.TypeAlias,
            ),
            payload=payload,
        )


class ScadaDBGCommands(Enum):
    show_subscriptions = "show_subscriptions"


class ScadaDBG(BaseModel):
    levels: LoggerLevels = LoggerLevels(
        message_summary=-1,
        lifecycle=-1,
        comm_event=-1,
    )
    command: Optional[ScadaDBGCommands] = None
    type_name: Literal["gridworks.scada.dbg.000"] = "gridworks.scada.dbg.000"

    @validator("command", pre=True)
    def command_value(cls, v):
        return as_enum(v, ScadaDBGCommands)
