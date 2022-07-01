"""gt.electric.meter.component.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_electric_meter_component.gt_electric_meter_component_base import (
    GtElectricMeterComponentBase,
)


class GtElectricMeterComponent(GtElectricMeterComponentBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.electric.meter.component.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
