from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from drivers.relay.relay_driver import RelayDriver
from gwproto.data_classes.components.relay_component import RelayComponent
from result import Ok, Result


class UnknownRelayDriver(RelayDriver):
    state: int

    def __init__(self, component: RelayComponent, settings: ScadaSettings):
        super(UnknownRelayDriver, self).__init__(component=component, settings=settings)
        self.state = 0

    def turn_on(self):
        self.state = 1

    def turn_off(self):
        self.state = 0

    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        return Ok(DriverResult(self.state))
