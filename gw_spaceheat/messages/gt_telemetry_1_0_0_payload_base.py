"""Base for gt.telemetry.1_0_0"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import datetime
import enum
import struct

from .property_format import is_reasonable_unix_time_ms


class TelemetryName(enum.Enum):
    WATER_FLOW_GPM_TIMES_100 = "WaterFlowGpmTimes100"

class GtTelemetry100PayloadBase(NamedTuple):
    Name: str     #
    Value: int     #
    ScadaReadTimeUnixMs: int     #
    MpAlias: str = 'gt.telemetry.1_0_0'

    def asdict(self):
        d = self._asdict()
        return d

    def is_telemetry_name(self, candidate):
        try:
            TelemetryName(candidate)
        except ValueError:
            return False
        return True


    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.telemetry.1_0_0':
            is_valid = False
            errors.append(f"Payload requires MpAlias of gt.telemetry.1_0_0, not {self.MpAlias}.")
        if not isinstance(self.Name, str):
            is_valid = False
            errors.append(f"Name {self.Name} must have type str.")
        if not self.is_telemetry_name(self.Name):
            is_valid = False
            errors.append(f"Name {self.Name} must be in list {[e.value for e in TelemetryName]}")
        if not isinstance(self.Value, int):
            is_valid = False
            errors.append(f"Value {self.Value} must have type int.")
        if not isinstance(self.ScadaReadTimeUnixMs, int):
            is_valid = False
            errors.append(f"ScadaSendTimeUnixMs {self.ScadaReadTimeUnixMs} must have type int.")
        if not is_reasonable_unix_time_ms(self.ScadaReadTimeUnixMs):
            is_valid = False
            errors.append(f"ScadaSendTimeUnixMs {self.ScadaReadTimeUnixMs} must have format ReasonableUnixTimeMs.")
        return is_valid, errors

