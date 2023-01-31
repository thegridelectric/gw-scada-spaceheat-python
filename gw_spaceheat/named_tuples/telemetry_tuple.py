from typing import NamedTuple
from data_classes.sh_node import ShNode
from schema.enums import TelemetryName
from schema.enums import Unit

class TelemetryTuple(NamedTuple):
    AboutNode: ShNode
    SensorNode: ShNode
    TelemetryName: TelemetryName

    def __repr__(self):
        return (
            f"TT({self.AboutNode.alias} {self.TelemetryName.value} read by {self.SensorNode.alias})"
        )


def unit_from_telemetry_name(tn: TelemetryName) -> Unit:
    if tn == TelemetryName.POWER_W:
        return Unit.W
    if tn == TelemetryName.WATER_TEMP_F_TIMES1000:
        return Unit.FAHRENHEIT
    if tn == TelemetryName.GALLONS_PER_MINUTE_TIMES10:
        return Unit.GPM
    if tn == TelemetryName.WATER_TEMP_C_TIMES1000:
        return Unit.CELCIUS
    if tn == TelemetryName.RELAY_STATE:
        return Unit.UNITLESS
    if tn == TelemetryName.CURRENT_RMS_MICRO_AMPS:
        return Unit.AMPS_RMS
    else:
        return Unit.UNITLESS


def exponent_from_telemetry_name(tn: TelemetryName) -> int:
    if tn == TelemetryName.POWER_W:
        return 0
    if tn == TelemetryName.WATER_TEMP_F_TIMES1000:
        return 3
    if tn == TelemetryName.GALLONS_PER_MINUTE_TIMES10:
        return 1
    if tn == TelemetryName.WATER_TEMP_C_TIMES1000:
        return 3
    if tn == TelemetryName.RELAY_STATE:
        return 0
    if tn == TelemetryName.CURRENT_RMS_MICRO_AMPS:
        return 6
    else:
        return 0