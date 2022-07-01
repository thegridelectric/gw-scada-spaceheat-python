"""Base for gt.sh.telemetry.from.multipurpose.sensor.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtShTelemetryFromMultipurposeSensorBase(NamedTuple):
    AboutNodeAliasList: List[str]
    ValueList: List[int]
    ScadaReadTimeUnixMs: int  #
    TelemetryNameList: List[TelemetryName]
    TypeAlias: str = "gt.sh.telemetry.from.multipurpose.sensor.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_gt(elt))
        d["TelemetryNameList"] = telemetry_name_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.AboutNodeAliasList, list):
            errors.append(
                f"AboutNodeAliasList {self.AboutNodeAliasList} must have type list."
            )
        else:
            for elt in self.AboutNodeAliasList:
                if not isinstance(elt, str):
                    errors.append(
                        f"elt {elt} of AboutNodeAliasList must have type str."
                    )
                if not property_format.is_lrd_alias_format(elt):
                    errors.append(
                        f"elt {elt} of AboutNodeAliasList must have format LrdAliasFormat"
                    )
        if not isinstance(self.ValueList, list):
            errors.append(
                f"ValueList {self.ValueList} must have type list."
            )
        else:
            for elt in self.ValueList:
                if not isinstance(elt, int):
                    errors.append(
                        f"elt {elt} of ValueList must have type int."
                    )
        if not isinstance(self.ScadaReadTimeUnixMs, int):
            errors.append(
                f"ScadaReadTimeUnixMs {self.ScadaReadTimeUnixMs} must have type int."
            )
        if not property_format.is_reasonable_unix_time_ms(self.ScadaReadTimeUnixMs):
            errors.append(
                f"ScadaReadTimeUnixMs {self.ScadaReadTimeUnixMs}"
                " must have format ReasonableUnixTimeMs"
            )
        if not isinstance(self.TelemetryNameList, list):
            errors.append(
                f"TelemetryNameList {self.TelemetryNameList} must have type list."
            )
        else:
            for elt in self.TelemetryNameList:
                if not isinstance(elt, TelemetryName):
                    errors.append(
                        f"elt {elt} of TelemetryNameList must have type TelemetryName."
                    )
        if self.TypeAlias != "gt.sh.telemetry.from.multipurpose.sensor.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.telemetry.from.multipurpose.sensor.100, not {self.TypeAlias}."
            )

        return errors
