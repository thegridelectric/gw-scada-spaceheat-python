"""Base for gt.pipe.flow.sensor.cac.100"""
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtPipeFlowSensorCac100Base(NamedTuple):
    ComponentAttributeClassId: str     #
    MakeModel: MakeModel     #
    DisplayName: Optional[str] = None
    CommsMethod: Optional[str] = None
    Alias: str = 'gt.pipe.flow.sensor.cac.100'

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        del(d["MakeModel"])
        d["SpaceheatMakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                          " must have format UuidCanonicalTextual")
        if self.CommsMethod:
            if not isinstance(self.CommsMethod, str):
                errors.append(f"CommsMethod {self.CommsMethod} must have type str.")
        if not isinstance(self.MakeModel, MakeModel):
            errors.append(f"MakeModel {self.MakeModel} must have type {MakeModel}.")
        if self.Alias != 'gt.pipe.flow.sensor.cac.100':
            errors.append(f"Type requires Alias of gt.pipe.flow.sensor.cac.100, not {self.Alias}.")
        
        return errors