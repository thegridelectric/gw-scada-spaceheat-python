"""gt.thermal.edge type"""

from schema.errors import MpSchemaError
from schema.gt.gt_thermal_edge.gt_thermal_edge_base import GtThermalEdgeBase


class GtThermalEdge(GtThermalEdgeBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.thermal.edge for {self}: {errors}")

    def hand_coded_errors(self):
        return []
