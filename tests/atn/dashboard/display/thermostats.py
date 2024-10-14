import time
from datetime import datetime
from typing import Self

from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.table import Table

from tests.atn.dashboard.channels.containers import Channels
from tests.atn.dashboard.channels.containers import PumpPowerState
from tests.atn.dashboard.display.styles import cold_style
from tests.atn.dashboard.display.styles import hot_style


class ThermostatDisplay:
    table: Table

    def __init__(self, channels: Channels):
        self.channels = channels
        self.update()

    def update(self) -> Self:
        self.table = Table()
        self.table.add_column("Thermostats", header_style="bold")
        self.table.add_column("Setpt", header_style="bold")
        self.table.add_column("HW Temp", header_style="bold")
        if len(self.channels.power.pumps.dist_pump_pwr_state_q) > 0:
            until = int(time.time())
            t = self.channels.power.pumps.dist_pump_pwr_state_q
            self.table.add_column("Heat Call", header_style="bold")
            for j in range(min(6, len(t))):
                start_s = t[j][2]
                minutes = int((until - start_s) / 60)
                if t[j][0] == PumpPowerState.Flow:
                    self.table.add_column(f"On {minutes}", header_style=hot_style)
                else:
                    self.table.add_column(f"Off {minutes}", header_style=cold_style)
                until = start_s
        for thermostat in self.channels.temperatures.thermostats:
            row = [
                thermostat.name,
                str(thermostat.set_point),
                str(thermostat.temperature),
            ]
            if len(self.channels.power.pumps.dist_pump_pwr_state_q) > 0:
                t = self.channels.power.pumps.dist_pump_pwr_state_q
                start_times = []
                for k in range(min(6, len(t))):
                    start_s = t[k][2]
                    start_times.append(datetime.fromtimestamp(start_s).strftime("%H:%M"))
                row.append("Start")
                row.extend(start_times)
            self.table.add_row(*row)
        return self

    def __rich_console__(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        yield self.table

