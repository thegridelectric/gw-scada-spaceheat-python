"""spaceheat.node.gt.100 type"""

from schema.errors import MpSchemaError
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_base import (
    SpaceheatNodeGtBase,
)

from schema.enums.role.role_map import Role


class SpaceheatNodeGt(SpaceheatNodeGtBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making spaceheat.node.gt.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return self.check_rated_voltage_existence()

    def check_rated_voltage_existence(self):
        """ SpaceheatNodes of role BoostElement must have a RatedVoltageV.
        For all other nodes RatedVoltageV is optional """
        if self.Role == Role.BOOST_ELEMENT and self.RatedVoltageV is None:
            return [f"{self.Alias} is a boost element. Must have RatedVoltageV"]
        return []
