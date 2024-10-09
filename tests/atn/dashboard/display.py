from gwproto.enums import TelemetryName
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.style import Style
from rich.table import Table
from rich.text import Text

from tests.atn.dashboard.channels import Channels

cold_style = Style(bold=True, color="#008000")
hot_style = Style(bold=True, color="dark_orange")
none_text = Text("NA", style="cyan")
# hot_ansii = "\033[31m"  # This red
hot_ansii = "\033[36m"  # temporary for Paul's purpose screen
# cold_ansii = "\033[34m"
cold_ansii = "\033[36m"  # temporary for Paul's purpose screen


class Displays:
    odds_and_ends: Table
    thermostat_table: Table
    power_table: Table
    picture: str

    def __init__(self, channels: Channels):
        self.update(channels)

    def update(self, channels: Channels):
        self.update_odds_and_ends(channels)
        self.update_thermostat_table(channels)
        self.update_power_table(channels)
        self.update_picture(channels)

    def __rich_console__(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        yield self.odds_and_ends
        yield self.thermostat_table
        yield self.power_table
        yield self.picture

    def update_odds_and_ends(self, channels: Channels):
        self.odds_and_ends = Table(
            title="Odds and Ends",
            title_justify="left",
            title_style="bold blue",
        )
        self.odds_and_ends.add_column("Channel", header_style="bold green", style="green")
        self.odds_and_ends.add_column("Value", header_style="bold dark_orange", style="dark_orange")
        self.odds_and_ends.add_column("Telemetry", header_style="bold green1", style="green1")
        for reading in channels.last_unused_readings:
            if reading.Telemetry in (
                TelemetryName.WaterTempCTimes1000,
                TelemetryName.AirTempCTimes1000
            ):
                value_str = f"{round((reading.Value * 9 / 5) + 32, 2)}"
                telemetry_str = "\u00b0F"
            else:
                value_str = str(reading.Value)
                telemetry_str = reading.Telemetry.value
            self.odds_and_ends.add_row(reading.ChannelName, value_str, telemetry_str)

    def update_thermostat_table(self, channels: Channels):
        self.thermostat_table = Table()
        self.thermostat_table.add_column("Stats", header_style="bold")
        self.thermostat_table.add_column("Setpt", header_style="bold")
        self.thermostat_table.add_column("HW Temp", header_style="bold")
        # self.thermostat_table.add_column("GW Temp", header_style="bold")

        # if len(self.dist_pump_pwr_state_q) > 0:
        #     until = int(time.time())
        #     t = self.dist_pump_pwr_state_q
        #     self.thermostat_table.add_column("Heat Call", header_style="bold")
        #     for j in range(min(6, len(t))):
        #         start_s = t[j][2]
        #         minutes = int((until - start_s) / 60)
        #         if t[j][0] == PumpPowerState.Flow:
        #             self.thermostat_table.add_column(f"On {minutes}", header_style=hot_style)
        #         else:
        #             self.thermostat_table.add_column(f"Off {minutes}", header_style=cold_style)
        #         until = start_s

        for thermostat in channels.thermostats:
            self.thermostat_table.add_row(
                thermostat.name,
                str(thermostat.set_point),
                str(thermostat.temperature)
            )
            # if j in stat_temp_f.keys():
            #     stat_row.append(f"{round(stat_temp_f[j], 1)}\u00b0F")

            # if len(self.dist_pump_pwr_state_q) > 0:
            #     t = self.dist_pump_pwr_state_q
            #     start_times = []
            #     for k in range(min(6, len(t))):
            #         start_s = t[k][2]
            #         start_times.append(pendulum.from_timestamp(start_s, tz='America/New_York').format('HH:mm'))
            #     stat_row.append("Start")
            #     stat_row.extend(start_times)

    def update_power_table(self, channels: Channels):
        self.power_table = Table()

        self.power_table.add_column("HP Power", header_style="bold")
        self.power_table.add_column("kW", header_style="bold")
        self.power_table.add_column("X", header_style="bold dark_orange", style="dark_orange")
        self.power_table.add_column("Pump", header_style="bold")
        self.power_table.add_column("Gpm", header_style="bold")
        self.power_table.add_column("Pwr (W)", header_style="bold")
        # power_table.add_column("HP State", header_style="bold dark_orange", style="bold dark_orange")
        #
        # extra_cols = min(len(self.hack_hp_state_q), 5)
        # for i in range(extra_cols):
        #     power_table.add_column(f"{self.hack_hp_state_q[i].state.value}", header_style="bold")
        #
        # hp_pwr_w_str = f"{round(self.hack_hp_state_q[0].hp_pwr_w / 1000, 2)}"
        # if self.hack_hp_state_q[0].idu_pwr_w is None:
        #     idu_pwr_w_str = none_text
        #     odu_pwr_w_str = none_text
        # else:
        #     idu_pwr_w_str = f"{round(self.hack_hp_state_q[0].idu_pwr_w / 1000, 2)}"
        #     odu_pwr_w_str = f"{round(self.hack_hp_state_q[0].odu_pwr_w / 1000, 2)}"

        # pump_pwr_str = {}
        # gpm_str = {}
        # for j in [0, 1, 2]:
        #     if pump_pwr_value[j] is None:
        #         pump_pwr_str[j] = "---"
        #     elif pump_pwr_value[j] < PUMP_OFF_THRESHOLD:
        #         pump_pwr_str[j] = "OFF"
        #     else:
        #         pump_pwr_str[j] = f"{round(pump_pwr_value[j], 2)}"
        #     flow_node = self.flow_nodes[j]
        #     try:
        #         idx = snap.AboutNodeAliasList.index(flow_node.alias)
        #         if snap.TelemetryNameList[idx] != TelemetryName.GallonsTimes100:
        #             raise Exception('Error in units. Expect TelemetryName.GallonsTimes100')
        #         delta_gallons = (snap.ValueList[idx] - prev_prev_snap.ValueList[idx]) / 100
        #         delta_min = (snap.ReportTimeUnixMs - prev_prev_snap.ReportTimeUnixMs) / 60_000
        #         speed = delta_gallons / delta_min
        #         if speed > 20:
        #             gpm_str[j] = "BAD"
        #         else:
        #             gpm_str[j] = f"{round(speed, 1)}"
        #     except:  # noqa
        #         gpm_str[j] = "NA"

        gpm_str = ["whoops-gpm-1", "whoops-gpm-2", "whoops-gpm-3"]
        pump_pwr_str = ["whoops-pump1", "whoops-pump2", "whoops-pump3"]
        row_1 = ["Hp Total", "whoops-hp-total", "x", "Primary", gpm_str[0], pump_pwr_str[0], "Started"]
        row_2 = ["Outdoor", str(channels.power.hp_outdoor), "x", "Dist", gpm_str[1], pump_pwr_str[1], "Tries"]
        row_3 = ["Indoor", str(channels.power.hp_indoor), "x", "Store", gpm_str[2], pump_pwr_str[2], "PumpPwr"]
        # for i in range(extra_cols):
        #     row_1.append(
        #         f"{pendulum.from_timestamp(self.hack_hp_state_q[i].state_start_s, tz='America/New_York').format('HH:mm')}")
        #     if (self.hack_hp_state_q[i].state == HackHpState.Idling
        #             or self.hack_hp_state_q[i].state == HackHpState.Trying):
        #         row_2.append(f"{self.hack_hp_state_q[i].start_attempts}")
        #     else:
        #         row_2.append(f"")
        #     row_3.append(f"{self.hack_hp_state_q[i].primary_pump_pwr_w} W")

        self.power_table.add_row(*row_1)
        self.power_table.add_row(*row_2)
        self.power_table.add_row(*row_3)

    def update_picture(self, channels: Channels):
        # hp_lwt_ansii = hot_ansii
        # hp_ewt_ansii = cold_ansii
        # if hp_lwt_f < hp_ewt_f - 1:
        #     hp_lwt_ansii = cold_ansii
        #     hp_ewt_ansii = hot_ansii
        # if hp_lwt_f < 100:
        #     hp_lwt_f_str = f" {hp_lwt_ansii}{round(hp_lwt_f, 1)}\u00b0F\033[0m"
        # else:
        #     hp_lwt_f_str = f"{hp_lwt_ansii}{round(hp_lwt_f, 1)}\u00b0F\033[0m"
        # if hp_ewt_f < 100:
        #     hp_ewt_f_str = f" {hp_ewt_ansii}{round(hp_ewt_f, 1)}\u00b0F\033[0m"
        # else:
        #     hp_ewt_f_str = f"{hp_ewt_ansii}{round(hp_ewt_f, 1)}\u00b0F\033[0m"
        #
        # dist_swt_ansii = hot_ansii
        # dist_rwt_ansii = cold_ansii
        #
        # if dist_swt_f < dist_rwt_f - 1:
        #     dist_swt_ansii = cold_ansii
        #     dist_rwt_ansii = hot_ansii
        # if dist_swt_f < 100:
        #     dist_swt_f_str = f" {dist_swt_ansii}{round(dist_swt_f, 1)}\u00b0F\033[0m"
        # else:
        #     dist_swt_f_str = f"{dist_swt_ansii}{round(dist_swt_f, 1)}\u00b0F\033[0m"
        # if dist_rwt_f < 100:
        #     dist_rwt_f_str = f" {dist_rwt_ansii}{round(dist_rwt_f, 1)}\u00b0F\033[0m"
        # else:
        #     dist_rwt_f_str = f"{dist_rwt_ansii}{round(dist_rwt_f, 1)}\u00b0F\033[0m"
        #
        # buffer_hot_ansii = hot_ansii
        # buffer_cold_ansii = cold_ansii
        # if buffer_hot_f < buffer_cold_f - 1:
        #     buffer_hot_ansii = cold_ansii
        #     buffer_cold_ansii = hot_ansii
        #
        # if buffer_hot_f < 100:
        #     buffer_hot_f_str = f" {buffer_hot_ansii}{round(buffer_hot_f, 1)}\u00b0F\033[0m"
        # else:
        #     buffer_hot_f_str = f"{buffer_hot_ansii}{round(buffer_hot_f, 1)}\u00b0F\033[0m"
        # if buffer_cold_f < 100:
        #     buffer_cold_f_str = f" {buffer_cold_ansii}{round(buffer_cold_f, 1)}\u00b0F\033[0m"
        # else:
        #     buffer_cold_f_str = f"{buffer_cold_ansii}{round(buffer_cold_f, 1)}\u00b0F\033[0m"
        #
        # store_hot_ansii = hot_ansii
        # store_cold_ansii = cold_ansii
        # if store_hot_f < store_cold_f - 1:
        #     store_hot_ansii = cold_ansii
        #     store_cold_ansii = hot_ansii
        #
        # if store_hot_f < 100:
        #     store_hot_f_str = f" {store_hot_ansii}{round(store_hot_f, 1)}\u00b0F\033[0m"
        # else:
        #     store_hot_f_str = f"{store_hot_ansii}{round(store_hot_f, 1)}\u00b0F\033[0m"
        # if store_cold_f < 100:
        #     store_cold_f_str = f" {store_cold_ansii}{round(store_cold_f, 1)}\u00b0F\033[0m"
        # else:
        #     store_cold_f_str = f"{store_cold_ansii}{round(store_cold_f, 1)}\u00b0F\033[0m"
        #
        # buff_temp_f_str = {}
        # for depth in range(1, 5):
        #     if depth in buff_temp_f:
        #         if buff_temp_f[depth] < 100:
        #             s = f" {round(buff_temp_f[depth], 1)}\u00b0F"
        #         else:
        #             s = f"{round(buff_temp_f[depth], 1)}\u00b0F"
        #     else:
        #         s = "  ---  "
        #     buff_temp_f_str[depth] = s
        #
        # # store_temp_f_str = {1: {}, 2: {}, 3: {}, 4: {}}
        # store_temp_f_str = defaultdict(dict)
        # for depth in range(1, 5):
        #     for tank in range(1, 4):
        #         if depth in store_temp_f and tank in store_temp_f[depth]:
        #             if store_temp_f[depth][tank] < 100:
        #                 s = f" {round(store_temp_f[depth][tank], 1)}\u00b0F"
        #             else:
        #                 s = f"{round(store_temp_f[depth][tank], 1)}\u00b0F"
        #         else:
        #             s = "  ---  "
        #         store_temp_f_str[depth][tank] = s

        # hack_hp_state = self.hack_hp_state_q[0]
        # if hack_hp_state.state == HackHpState.Heating:
        #     heating = True
        # else:
        #     heating = False
        #
        # if heating is True:
        #     hp_health_comment_1 = ""
        #     hp_health_comment_2 = ""
        # else:
        #     hp_health_comment_1 = f"{hack_hp_state.state.value}."
        #     last_heating = next((x for x in self.hack_hp_state_q if x.state == HackHpState.Heating), None)
        #     hp_health_comment_2 = ""
        #     if last_heating is not None:
        #         if last_heating.state_end_s:
        #             hp_health_comment_2 += f"Last time heating: {pendulum.from_timestamp(last_heating.state_end_s, tz='America/New_York').format('HH:mm')}. "
        #     if hack_hp_state.start_attempts == 1:
        #         hp_health_comment_2 += f"1 start attempt."
        #     elif hack_hp_state.start_attempts > 1:
        #         hp_health_comment_2 += f"{hack_hp_state.start_attempts} start attempts."
        # atn_alias = self.layout.atn_g_node_alias
        # short_name = atn_alias.split(".")[-1]
        # return f"""{short_name}:
        #                                  {hp_lwt_ansii}HP LWT\033[0m   ┏━━━━━┓   {hp_health_comment_1}
        #                                ┏━{hp_lwt_f_str}━━┃ HP  ┃   {hp_health_comment_2}
        #   {buffer_hot_ansii}Buff Hot\033[0m ━━┓                 ┃    ┏─────┃     ┃   Lift: {round(hp_lwt_f - hp_ewt_f, 1)}\u00b0F
        #    {buffer_hot_f_str}   ┃                 ┃ {hp_ewt_ansii}HP EWT\033[0m   └─────┘
        #  ┏━━━━━━━━━┓ ▼                 ┃ {hp_ewt_f_str}
        #  ┃  Buffer ┃━━━━━━━━━┳━ ISO ━━─┴─━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        #  ┡━━━━━━━━━┩         ┃              │         ┏━━━━━━━━━┓   ┏━━━━━━━━━┓   ┏━━━━━━━━━┓    ┃
        #  │ {buff_temp_f_str[1]} │       {dist_swt_ansii}Dist FWT\033[0m         │         ┃  Tank3  ┃   ┃  Tank2  ┃   ┃  Tank1  ┃    ┃
        #  │ {buff_temp_f_str[2]} │       {dist_swt_f_str}          │         ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━━━{store_hot_f_str}
        #  │ {buff_temp_f_str[3]} │         ┃              │         │ {store_temp_f_str[1][3]} │ │ │ {store_temp_f_str[1][2]} │ │ │ {store_temp_f_str[1][1]} │
        #  │ {buff_temp_f_str[4]} │────┓    ┃              │         │ {store_temp_f_str[2][3]} │ │ │ {store_temp_f_str[2][2]} │ │ │ {store_temp_f_str[2][1]} │
        #  └─────────┘ ▲  │    ┃              │         │ {store_temp_f_str[3][3]} │ │ │ {store_temp_f_str[3][2]} │ │ │ {store_temp_f_str[3][1]} │
        #   {buffer_cold_ansii}Buff Cold\033[0m  │  ┡────┃──────────────┴─{store_cold_f_str}─│ {store_temp_f_str[4][3]} │ └━│ {store_temp_f_str[4][2]} │ └━│ {store_temp_f_str[4][1]} │
        #    {buffer_cold_f_str} ──┘  │    ┃                        └─────────┘   └─────────┘   └─────────┘
        #             {dist_rwt_ansii}Dist RWT\033[0m ┃
        #             {dist_rwt_f_str}  ┃  Emitter \u0394 = {round(dist_swt_f - dist_rwt_f, 1)}\u00b0F
        # """
        self.picture = f"""
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  hi ho hi ho, it's off to plot I go  ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        
        Thermostats: {len(channels.thermostats)}
        """