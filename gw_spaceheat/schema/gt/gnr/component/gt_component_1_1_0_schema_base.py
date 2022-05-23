"""SchemaBase for gt.component.1_1_0"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import schema.property_format


class SchemaBase(NamedTuple):
    ComponentId: str     #
    DisplayName: str     #
    ComponentAttributeClassId: str     #
    YmdWeatherUid: Optional[str] = None
    AnnualHvacKwhThYmd: Optional[int] = None
    GNodeId: Optional[str] = None
    HeatCapacityWhPerDegF: Optional[int] = None
    StaticSpaceHeatThermostatSetpointF: Optional[float] = None
    ZeroHeatDeltaF: Optional[int] = None
    MixingValveTempF: Optional[int] = None
    MpAlias: str = 'gt.component.1_1_0'

    def asdict(self):
        d = self._asdict()
        if d["YmdWeatherUid"] is None:
            del d["YmdWeatherUid"]
        if d["AnnualHvacKwhThYmd"] is None:
            del d["AnnualHvacKwhThYmd"]
        if d["GNodeId"] is None:
            del d["GNodeId"]
        if d["HeatCapacityWhPerDegF"] is None:
            del d["HeatCapacityWhPerDegF"]
        if d["StaticSpaceHeatThermostatSetpointF"] is None:
            del d["StaticSpaceHeatThermostatSetpointF"]
        if d["ZeroHeatDeltaF"] is None:
            del d["ZeroHeatDeltaF"]
        if d["MixingValveTempF"] is None:
            del d["MixingValveTempF"]
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.1_1_0':
            is_valid = False
            errors.append(f"Payload requires MpAlias of gt.component.1_1_0, not {self.MpAlias}.")
        if not isinstance(self.ComponentId, str):
            is_valid = False
            errors.append(f"ComponentId {self.ComponentId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentId):
            is_valid = False
            errors.append(f"ComponentId {self.ComponentId} must have format UuidCanonicalTextual.")
        if not isinstance(self.DisplayName, str):
            is_valid = False
            errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.ComponentAttributeClassId, str):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have format UuidCanonicalTextual.")
        if self.YmdWeatherUid:
            if not isinstance(self.YmdWeatherUid, str):
                is_valid = False
                errors.append(f"YmdWeatherUid {self.YmdWeatherUid} must have type str.")
        if self.AnnualHvacKwhThYmd:
            if not isinstance(self.AnnualHvacKwhThYmd, int):
                is_valid = False
                errors.append(f"AnnualHvacKwhThYmd {self.AnnualHvacKwhThYmd} must have type int.")
        if self.GNodeId:
            if not isinstance(self.GNodeId, str):
                is_valid = False
                errors.append(f"GNodeId {self.GNodeId} must have type str.")
            if not schema.property_format.is_uuid_canonical_textual(self.GNodeId):
                is_valid = False
                errors.append(f"GNodeId {self.GNodeId} must have format UuidCanonicalTextual.")
        if self.HeatCapacityWhPerDegF:
            if not isinstance(self.HeatCapacityWhPerDegF, int):
                is_valid = False
                errors.append(f"HeatCapacityWhPerDegF {self.HeatCapacityWhPerDegF} must have type int.")
        if self.StaticSpaceHeatThermostatSetpointF:
            if not isinstance(self.StaticSpaceHeatThermostatSetpointF, float):
                is_valid = False
                errors.append(f"StaticSpaceHeatThermostatSetpointF {self.StaticSpaceHeatThermostatSetpointF} must have type float.")
        if self.ZeroHeatDeltaF:
            if not isinstance(self.ZeroHeatDeltaF, int):
                is_valid = False
                errors.append(f"ZeroHeatDeltaF {self.ZeroHeatDeltaF} must have type int.")
        if self.MixingValveTempF:
            if not isinstance(self.MixingValveTempF, int):
                is_valid = False
                errors.append(f"MixingValveTempF {self.MixingValveTempF} must have type int.")
        return is_valid, errors

