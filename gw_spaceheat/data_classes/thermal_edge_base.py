"""ThermalEdgeBase definition"""

from abc import ABC, abstractmethod
from typing import Optional, Dict

from schema.gt.gt_thermal_edge.gt_thermal_edge import GtThermalEdge
from data_classes.errors import DcError


class ThermalEdgeBase(ABC):
    _by_id: Dict = {}
    base_props = []
    base_props.append("thermal_edge_id")

    def __init__(self,
                 thermal_edge_id: str,
                 ):
        self.thermal_edge_id = thermal_edge_id   #
        ThermalEdgeBase._by_id[self.thermal_edge_id] = self

    def update(self, type: GtThermalEdge):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtThermalEdge):
        pass

    @abstractmethod
    def _check_update_axioms(self, type: GtThermalEdge):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
