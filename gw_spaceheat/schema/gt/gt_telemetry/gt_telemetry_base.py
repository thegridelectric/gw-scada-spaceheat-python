"""Base for gt.telemetry.110"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtTelemetryBase(NamedTuple):
    ScadaReadTimeUnixMs: int  #
    Value: int  #
    Name: TelemetryName  #
    Exponent: int  #
    TypeAlias: str = "gt.telemetry.110"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["Name"]
        d["NameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.Name)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ScadaReadTimeUnixMs, int):
            errors.append(
                f"ScadaReadTimeUnixMs {self.ScadaReadTimeUnixMs} must have type int."
            )
        if not property_format.is_reasonable_unix_time_ms(self.ScadaReadTimeUnixMs):
            errors.append(
                f"ScadaReadTimeUnixMs {self.ScadaReadTimeUnixMs}"
                " must have format ReasonableUnixTimeMs"
            )
        if not isinstance(self.Value, int):
            errors.append(
                f"Value {self.Value} must have type int."
            )
        if not isinstance(self.Name, TelemetryName):
            errors.append(
                f"Name {self.Name} must have type {TelemetryName}."
            )
        if not isinstance(self.Exponent, int):
            errors.append(
                f"Exponent {self.Exponent} must have type int."
            )
        if self.TypeAlias != "gt.telemetry.110":
            errors.append(
                f"Type requires TypeAlias of gt.telemetry.110, not {self.TypeAlias}."
            )

        return errors
