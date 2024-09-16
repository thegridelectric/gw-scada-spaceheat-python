import time

from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from drivers.relay.relay_driver import RelayDriver
from enums import MakeModel
from gwproto.data_classes.components.relay_component import RelayComponent
from result import Ok, Result


class GridworksSimBool30AmpRelay_RelayDriver(RelayDriver):
    def __init__(self, component: RelayComponent, settings: ScadaSettings):
        super(GridworksSimBool30AmpRelay_RelayDriver, self).__init__(
            component=component, settings=settings
        )
        if component.cac.MakeModel != MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            raise Exception(
                f"Expected {MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY}, got {component.cac}"
            )
        self.component = component
        self._fake_relay_state = 0

    def cmd_delay(self):
        delay_s = self.component.cac.TypicalResponseTimeMs / 1000
        time.sleep(delay_s)

    def turn_on(self):
        self.cmd_delay()
        self._fake_relay_state = 1

    def turn_off(self):
        self.cmd_delay()
        self._fake_relay_state = 0

    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        self.cmd_delay()
        return Ok(DriverResult(self._fake_relay_state))
