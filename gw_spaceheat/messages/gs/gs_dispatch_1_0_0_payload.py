"""GridWorks serial message protocol GsPwr100 with MpAlias p"""
from typing import List, Dict, Tuple, Optional
from messages.gs.gs_pwr_1_0_0_payload_base import GsPwrPayload100Base

class GsPwr100Payload(GsPwrPayload100Base):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making p payload.')
        return is_valid, errors

    # hand-code schema axiom validations below