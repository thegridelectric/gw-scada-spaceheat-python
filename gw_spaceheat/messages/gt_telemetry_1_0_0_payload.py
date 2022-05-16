"""Payload for gt.telemetry.1_0_0"""
from typing import List, Dict, Tuple, Optional
from .gt_telemetry_1_0_0_payload_base import GtTelemetry100PayloadBase, TelemetryName

class GtTelemetry100Payload(GtTelemetry100PayloadBase):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.telemetry.1_0_0 payload.')
        return is_valid, errors

    # hand-code schema axiom validations below