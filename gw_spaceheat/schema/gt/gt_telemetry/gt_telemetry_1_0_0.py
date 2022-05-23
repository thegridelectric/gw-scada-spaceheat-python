"""gt.telemetry.100 type"""
from typing import List, Tuple, Optional
from schema.gt.gt_telemetry.gt_telemetry_1_0_0_base import GtTelemetry100Base


class GtTelemetry100(GtTelemetry100Base):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.telemetry.100 type.')
        return is_valid, errors

    # hand-code schema axiom validations below