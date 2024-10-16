from typing import Deque
from typing import Self

from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult

from tests.atn.atn_config import DashboardSettings
from tests.atn.dashboard.display.odds_and_ends import OddsAndEnds
from tests.atn.dashboard.display.power import PowerDisplay
from tests.atn.dashboard.display.thermostats import ThermostatDisplay
from tests.atn.dashboard.display.ascii_picture import AsciiPicture
from tests.atn.dashboard.channels.containers import Channels
from tests.atn.dashboard.hackhp import HackHpStateCapture

class Displays:
    odds_and_ends: OddsAndEnds
    thermostat: ThermostatDisplay
    power: PowerDisplay
    ascii_picture: AsciiPicture

    def __init__(
            self,
            settings: DashboardSettings,
            short_name: str,
            channels: Channels,
            hack_hp_state_q: Deque[HackHpStateCapture]
    ) -> None:
        self.odds_and_ends = OddsAndEnds(channels)
        self.thermostat = ThermostatDisplay(channels)
        self.power = PowerDisplay(
            channels,
            print_hack_hp=settings.print_hack_hp,
            hack_hp_state_q=hack_hp_state_q,
        )
        self.ascii_picture = AsciiPicture(short_name, channels, hack_hp_state_q)
        self.update()

    def update(self) -> Self:
        self.odds_and_ends.update()
        self.thermostat.update()
        self.power.update()
        self.ascii_picture.update()
        return self

    def __rich_console__(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        yield ""
        yield self.odds_and_ends
        yield self.thermostat
        yield self.power
        yield self.ascii_picture




