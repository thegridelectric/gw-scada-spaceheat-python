"""ElectricMeterComponentBase definition"""

from abc import abstractmethod
from typing import Optional

from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.component import Component
from data_classes.errors import DcError
from schema.enums.make_model.make_model_map import MakeModel
from schema.gt.gt_electric_meter_component.gt_electric_meter_component import (
    GtElectricMeterComponent,
)


class ElectricMeterComponentBase(Component):
    base_props = []
    base_props.append("display_name")
    base_props.append("component_id")
    base_props.append("hw_uid")
    base_props.append("component_attribute_class_id")

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str] = None,
        hw_uid: Optional[str] = None,
    ):

        super(ElectricMeterComponentBase, self).__init__(
            component_id=component_id,
            display_name=display_name,
            component_attribute_class_id=component_attribute_class_id,
            hw_uid=hw_uid,
        )
        self.hw_uid = hw_uid
        self.component_attribute_class_id = component_attribute_class_id

    def update(self, gw_tuple: GtElectricMeterComponent):
        self._check_immutability_constraints(gw_tuple=gw_tuple)
        self._check_update_axioms(gw_tuple=gw_tuple)

    def _check_immutability_constraints(self, gw_tuple: GtElectricMeterComponent):
        if self.component_id != gw_tuple.ComponentId:
            raise DcError(
                f"component_id must be immutable for {self}. " f"Got {gw_tuple.ComponentId}"
            )
        if self.component_attribute_class_id != gw_tuple.ComponentAttributeClassId:
            raise DcError(
                f"component_attribute_class must be immutable for {self}. "
                f"Got {gw_tuple.ComponentAttributeClassId}"
            )
        if self.hw_uid:
            if self.hw_uid != gw_tuple.HwUid:
                raise DcError(f"hw_uid must be immutable for {self}. " f"Got {gw_tuple.HwUid}")

    @property
    def cac(self) -> ElectricMeterCac:
        return ElectricMeterCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    @abstractmethod
    def _check_update_axioms(self, gw_tuple: GtElectricMeterComponent):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
