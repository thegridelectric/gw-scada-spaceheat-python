"""GridWorks serial message protocol gs.pwr.100 with MpAlias p"""
from typing import List, Dict, Tuple, Optional
from schema.gs.gs_pwr_1_0_0_base import GsPwr100Base

class GsPwr100(GsPwr100Base):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gs.pwr.100 type')
        return is_valid, errors

    # hand-code schema axiom validations below