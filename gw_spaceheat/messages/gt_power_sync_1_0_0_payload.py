"""Payload for gt.power.sync.1_0_0"""
from typing import List, Dict, Tuple, Optional
from messages.gt_power_sync_1_0_0_payload_base import GtPowerSync100PayloadBase

class GtPowerSync100Payload(GtPowerSync100PayloadBase):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.power.sync.1_0_0 payload.')
        return is_valid, errors

    # hand-code schema axiom validations below