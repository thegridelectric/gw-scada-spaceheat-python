"""ElectricHeaterCacBase definition"""

from abc import abstractmethod
from typing import Optional, Dict

from schema.gt.gt_electric_heater_cac.gt_electric_heater_cac_100 import GtElectricHeaterCac100
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError
from schema.enums.make_model.make_model_map import MakeModelMap


class ElectricHeaterCacBase(ComponentAttributeClass):
    _by_id: Dict = {}
    base_props = []

    base_props.append("component_attribute_class_id")
    base_props.append("make_model")
    base_props.append("display_name")

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 ):

        super(ElectricHeaterCacBase, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                                    display_name=display_name)
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)   #
        ElectricHeaterCacBase._by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def update(self, type: GtElectricHeaterCac100):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtElectricHeaterCac100):
        if self.component_attribute_class_id != type.ComponentAttributeClassId:
            raise DcError(f'component_attribute_class_id must be immutable for {self}. '
                          f'Got {type.ComponentAttributeClassId}')
        if self.make_model != type.MakeModel:
            raise DcError(f'make_model must be immutable for {self}. '
                          f'Got {type.MakeModel}')

    @abstractmethod
    def _check_update_axioms(self, type: GtElectricHeaterCac100):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
