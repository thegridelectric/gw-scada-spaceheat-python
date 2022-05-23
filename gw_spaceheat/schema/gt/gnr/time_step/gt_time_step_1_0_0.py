"""gt.time.step.100 type"""
from typing import List, Tuple, Optional
from schema.gt.gnr.time_step.gt_time_step_1_0_0_base import GtTimeStep100Base


class GtTimeStep100(GtTimeStep100Base):

    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.time.step.100 type.')
        return is_valid, errors

    # hand-code schema axiom validations below