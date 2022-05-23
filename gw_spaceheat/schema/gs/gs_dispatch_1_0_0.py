"""GridWorks serial message protocol GsPwr100 with MpAlias d"""
from typing import List, Dict, Tuple, Optional
from schema.gs.gs_dispatch_1_0_0_base import GsDispatch100Base

class GsDispatch100(GsDispatch100Base):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gs.dispatch.100 type')
        return is_valid, errors

    # hand-code schema axiom validations below