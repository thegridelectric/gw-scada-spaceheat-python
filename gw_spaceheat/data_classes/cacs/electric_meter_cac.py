"""ElectricMeterCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.electric_meter_cac_base import ElectricMeterCacBase
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac import GtElectricMeterCac


class ElectricMeterCac(ElectricMeterCacBase):
    by_id: Dict[str, "ElectricMeterCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 comms_method: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             comms_method=comms_method,
                                             display_name=display_name,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )
        ElectricMeterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: GtElectricMeterCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"

    @property
    def telemetry_name(self):
        return TelemetryName.POWER_W