"""gt.sh.node.120 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_node.gt_sh_node_base import (
    GtShNodeBase,
)


class GtShNode(GtShNodeBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.sh.node.120 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
