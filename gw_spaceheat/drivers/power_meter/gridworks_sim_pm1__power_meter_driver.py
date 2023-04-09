from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from drivers.power_meter.power_meter_driver import PowerMeterDriver
from enums import MakeModel
from gwproto.data_classes.components.electric_meter_component import (
    ElectricMeterComponent,
)
from result import Ok, Result


class GridworksSimPm1_PowerMeterDriver(PowerMeterDriver):
    def __init__(self, component: ElectricMeterComponent, settings: ScadaSettings):
        super(GridworksSimPm1_PowerMeterDriver, self).__init__(
            component=component, settings=settings
        )
        if component.cac.make_model != MakeModel.GRIDWORKS__SIMPM1:
            raise Exception(
                f"Expected {MakeModel.GRIDWORKS__SIMPM1}, got {component.cac}"
            )
        self.component = component
        self.fake_current_rms_micro_amps = 18000
        self.fake_power_w = 0

    def read_hw_uid(self) -> Result[DriverResult[str | None], Exception]:
        return Ok(DriverResult("1001ab"))

    def read_power_w(self, ShNode) -> Result[DriverResult[int | None], Exception]:
        return Ok(DriverResult(self.fake_power_w))

    def read_current_rms_micro_amps(
        self, ShNode
    ) -> Result[DriverResult[int | None], Exception]:
        return Ok(DriverResult(self.fake_current_rms_micro_amps))
