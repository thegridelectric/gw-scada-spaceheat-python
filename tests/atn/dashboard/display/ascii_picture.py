from datetime import datetime
from typing import Deque
from typing import Self

from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult

from tests.atn.dashboard.display.styles import cold_ansii
from tests.atn.dashboard.display.styles import hot_ansii
from tests.atn.dashboard.hackhp import HackHpState
from tests.atn.dashboard.hackhp import HackHpStateCapture
from tests.atn.dashboard.channels.containers import Channels


class AsciiPicture:
    short_name: str
    channels: Channels
    ascii_picture: str

    def __init__(self, short_name: str, channels: Channels, hack_hp_state_q: Deque[HackHpStateCapture]):
        self.short_name = short_name
        self.channels = channels
        self.hack_hp_state_q = hack_hp_state_q
        self.ascii_picture = ""

    def update(self) -> Self:
        temperatures = self.channels.temperatures
        hp_lwt = temperatures.hp_lwt
        hp_ewt = temperatures.hp_ewt
        dist_swt = temperatures.dist_swt
        dist_rwt = temperatures.dist_rwt
        buff_hot = temperatures.buffer_hot_pipe
        buff_cold = temperatures.buffer_cold_pipe
        store_hot = temperatures.store_hot_pipe
        store_cold = temperatures.store_cold_pipe
        hp_lwt_color, hp_ewt_color = self._hot_cold_colors("hp_lwt", "hp_ewt")
        dist_swt_color, dist_rwt_color = self._hot_cold_colors("dist_swt", "dist_rwt")
        buff_hot_color, buff_cold_color = self._hot_cold_colors("buffer_hot_pipe", "buffer_cold_pipe")
        store_hot_color, store_cold_color = self._hot_cold_colors("store_hot_pipe", "store_cold_pipe")
        hp_health_1, hp_health_2 = self._hp_hack_comments()
        lift = self._temp_diff("hp_lwt", "hp_ewt")
        emitter = self._temp_diff("dist_swt", "dist_rwt")
        tanks = temperatures.tanks
        buff = tanks.buffer
        store1 = tanks.store[0]
        store2 = tanks.store[1]
        store3 = tanks.store[2]
        self.ascii_picture = f"""{self.short_name}:
                                 {hp_lwt_color}HP LWT\033[0m   ┏━━━━━┓   {hp_health_1}
                               ┏━{hp_lwt}━━┃ HP  ┃   {hp_health_2}
  {buff_hot_color}Buff Hot\033[0m ━━┓                 ┃    ┏─────┃     ┃   Lift: {lift}\u00b0F
   {buff_hot}   ┃                 ┃ {hp_ewt_color}HP EWT\033[0m   └─────┘
 ┏━━━━━━━━━┓ ▼                 ┃ {hp_ewt}
 ┃  Buffer ┃━━━━━━━━━┳━ ISO ━━─┴─━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 ┡━━━━━━━━━┩         ┃              │         ┏━━━━━━━━━┓   ┏━━━━━━━━━┓   ┏━━━━━━━━━┓    ┃
 │ {buff.depth1} │       {dist_swt_color}Dist FWT\033[0m         │         ┃  Tank3  ┃   ┃  Tank2  ┃   ┃  Tank1  ┃    ┃
 │ {buff.depth1} │       {dist_swt}          │         ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━━━{store_hot_color}{store_hot}
 │ {buff.depth1} │         ┃              │         │ {store3.depth1} │ │ │ {store2.depth1} │ │ │ {store1.depth1} │
 │ {buff.depth1} │────┓    ┃              │         │ {store3.depth2} │ │ │ {store2.depth2} │ │ │ {store1.depth2} │
 └─────────┘ ▲  │    ┃              │         │ {store3.depth3} │ │ │ {store2.depth3} │ │ │ {store1.depth3} │
  {buff_cold_color}Buff Cold\033[0m  │  ┡────┃──────────────┴─{store_cold_color}{store_cold}─│ {store3.depth4} │ └━│ {store2.depth4} │ └━│ {store1.depth4} │
   {buff_cold} ──┘  │    ┃                        └─────────┘   └─────────┘   └─────────┘
            {dist_rwt_color}Dist RWT\033[0m ┃
            {dist_rwt}  ┃  Emitter \u0394 = {emitter}\u00b0F
"""
        return self

    def _hot_cold_colors(self, hot:str, cold: str) -> tuple[str, str]:
        hot_f = getattr(self.channels.temperatures, hot).converted
        cold_f = getattr(self.channels.temperatures, cold).converted
        if hot_f is not None and cold_f is not None and hot_f < cold_f - 1:
            return cold_ansii, hot_ansii
        return hot_ansii, cold_ansii

    def _temp_diff(self, hot:str, cold:str) -> str:
        hot_f = getattr(self.channels.temperatures, hot).converted
        cold_f = getattr(self.channels.temperatures, cold).converted
        if hot_f is not None and cold_f is not None and hot_f < cold_f - 1:
            return f"{round(hot_f - cold_f, 1):3.1f}"
        return " --- "

    def _hp_hack_comments(self) -> tuple[str, str]:
        hack_hp_state = self.hack_hp_state_q[0]
        if hack_hp_state.state == HackHpState.Heating:
            heating = True
        else:
            heating = False
        if heating is True:
            hp_health_comment_1 = ""
            hp_health_comment_2 = ""
        else:
            hp_health_comment_1 = f"{hack_hp_state.state.value}."
            last_heating = next((x for x in self.hack_hp_state_q if x.state == HackHpState.Heating), None)
            hp_health_comment_2 = ""
            if last_heating is not None:
                if last_heating.state_end_s:
                    hp_health_comment_2 += f"Last time heating: {datetime.fromtimestamp(last_heating.state_end_s).strftime('%H:%M')}. "
            if hack_hp_state.start_attempts == 1:
                hp_health_comment_2 += "1 start attempt."
            elif hack_hp_state.start_attempts > 1:
                hp_health_comment_2 += f"{hack_hp_state.start_attempts} start attempts."
        return hp_health_comment_1, hp_health_comment_2

    def __rich_console__(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        yield self.ascii_picture

