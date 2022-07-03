"""gt.electric.heater.component.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_electric_heater_component.gt_electric_heater_component_base import (
    GtElectricHeaterComponentBase,
)


class GtElectricHeaterComponent(GtElectricHeaterComponentBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.electric.heater.component.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
