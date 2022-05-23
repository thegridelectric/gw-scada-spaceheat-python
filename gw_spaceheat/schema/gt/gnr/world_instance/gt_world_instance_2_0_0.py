"""gt.world.instance.200 type"""
from typing import List, Tuple, Optional
from schema.gt.gnr.world_instance.gt_world_instance_2_0_0_base import GtWorldInstance200Base


class GtWorldInstance200(GtWorldInstance200Base):

    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.world.instance.200 type.')
        return is_valid, errors

    # hand-code schema axiom validations below