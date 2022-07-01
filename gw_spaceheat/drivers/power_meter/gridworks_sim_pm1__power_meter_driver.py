from typing import Optional
from drivers.power_meter.power_meter_driver import PowerMeterDriver
from data_classes.components.electric_meter_component import ElectricMeterComponent

from schema.enums.make_model.make_model_map import MakeModel


class GridworksSimPm1_PowerMeterDriver(PowerMeterDriver):
    def __init__(self, component: ElectricMeterComponent):
        super(GridworksSimPm1_PowerMeterDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.GRIDWORKS__SIMPM1:
            raise Exception(f"Expected {MakeModel.GRIDWORKS__SIMPM1}, got {component.cac}")
        self.component = component
        self._fake_current_rms_micro_amps = 18000

    def read_current_rms_micro_amps(self) -> Optional[int]:
        return self._fake_current_rms_micro_amps

    def read_hw_uid(self) -> Optional[str]:
        return "1001ab"

    def read_power_w(self) -> Optional[int]:
        return None
