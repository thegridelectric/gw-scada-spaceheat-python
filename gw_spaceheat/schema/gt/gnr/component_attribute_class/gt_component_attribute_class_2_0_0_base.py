"""Base for gt.component.attribute.class.200"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format
from schema.gt.gnr.component_type.gt_component_type_1_0_0 import GtComponentType100


class GtComponentAttributeClass200Base(NamedTuple):
    ComponentType: GtComponentType100     #
    ComponentAttributeClassId: str     #
    MakeModel: str     #
    RatedPowerWithdrawnVa: Optional[int] = None
    SeriesReactanceOhms: Optional[float] = None
    ResistanceOhms: Optional[float] = None
    RatedPowerInjectedVa: Optional[int] = None
    MpAlias: str = 'gt.component.attribute.class.200'

    def asdict(self):
        d = self._asdict()
        if d["RatedPowerWithdrawnVa"] is None:
            del d["RatedPowerWithdrawnVa"]
        if d["SeriesReactanceOhms"] is None:
            del d["SeriesReactanceOhms"]
        if d["ResistanceOhms"] is None:
            del d["ResistanceOhms"]
        if d["RatedPowerInjectedVa"] is None:
            del d["RatedPowerInjectedVa"]
        d['ComponentType'] = d['ComponentType'].asdict()
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.attribute.class.200':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.component.attribute.class.200, not {self.MpAlias}.")
        if not isinstance(self.ComponentAttributeClassId, str):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have format UuidCanonicalTextual.")
        if not isinstance(self.MakeModel, str):
            is_valid = False
            errors.append(f"MakeModel {self.MakeModel} must have type str.")
        if not isinstance(self.ComponentType, GtComponentType100):
            is_valid = False
            raise Exception(f"Make sure ComponentType has type GtComponentType100")
        new_is_valid, new_errors = self.ComponentType.is_valid()
        if not new_is_valid:
            is_valid = False
            errors += new_errors
        if self.RatedPowerWithdrawnVa:
            if not isinstance(self.RatedPowerWithdrawnVa, int):
                is_valid = False
                errors.append(f"RatedPowerWithdrawnVa {self.RatedPowerWithdrawnVa} must have type int.")
        if self.SeriesReactanceOhms:
            if not isinstance(self.SeriesReactanceOhms, float):
                is_valid = False
                errors.append(f"SeriesReactanceOhms {self.SeriesReactanceOhms} must have type float.")
        if self.ResistanceOhms:
            if not isinstance(self.ResistanceOhms, float):
                is_valid = False
                errors.append(f"ResistanceOhms {self.ResistanceOhms} must have type float.")
        if self.RatedPowerInjectedVa:
            if not isinstance(self.RatedPowerInjectedVa, int):
                is_valid = False
                errors.append(f"RatedPowerInjectedVa {self.RatedPowerInjectedVa} must have type int.")
        return is_valid, errors

