"""ElectricMeterCacBase definition"""

from abc import abstractmethod
from typing import Optional, Dict

from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac import GtElectricMeterCac
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError
from schema.enums.local_comm_interface.local_comm_interface_map import LocalCommInterfaceMap
from schema.enums.make_model.make_model_map import MakeModelMap


class ElectricMeterCacBase(ComponentAttributeClass):
    base_props = []
    
    base_props.append("component_attribute_class_id")
    base_props.append("local_comm_interface")
    base_props.append("make_model")
    base_props.append("display_name")
    base_props.append("default_baud")
    base_props.append("update_period_ms")

    def __init__(self, component_attribute_class_id: str,
                 local_comm_interface_gt_enum_symbol: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 default_baud: Optional[int] = None,
                 update_period_ms: Optional[int] = None,
                 ):

        super(ElectricMeterCacBase, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name)
        self.default_baud = default_baud
        self.update_period_ms = update_period_ms
        self.local_comm_interface = LocalCommInterfaceMap.gt_to_local(local_comm_interface_gt_enum_symbol)
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)

    def update(self, type: GtElectricMeterCac):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtElectricMeterCac):
        if self.component_attribute_class_id != type.ComponentAttributeClassId:
            raise DcError(f'component_attribute_class_id must be immutable for {self}. '
                          f'Got {type.ComponentAttributeClassId}')
        if self.make_model != type.MakeModel:
            raise DcError(f'make_model must be immutable for {self}. '
                          f'Got {type.MakeModel}')

    @abstractmethod
    def _check_update_axioms(self, type: GtElectricMeterCac):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
