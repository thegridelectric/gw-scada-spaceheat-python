from typing import Dict, List

DEFAULT_ANALOG_READER = "analog-temp"
from gwproto.data_classes.telemetry_tuple import ChannelStub
from gwproto.enums import TelemetryName


class ZoneName:
    def __init__(self, zone: str, idx: int):
        zone_name = f"zone{idx + 1}-{zone}".lower()
        self.zone_name = zone_name
        self.stat = f"{zone_name}-stat"

    def __repr__(self) -> str:
        return f"Zone {self.zone_name} and stat {self.stat}"


class TankNodes:
    def __init__(self, tank_name: str):
        self.reader = tank_name
        self.depth1 = f"{tank_name}-depth1"
        self.depth2 = f"{tank_name}-depth2"
        self.depth3 = f"{tank_name}-depth3"
        self.depth4 = f"{tank_name}-depth4"

    def __repr__(self) -> str:
        return f"{self.reader} reads {self.depth1}, {self.depth2}, {self.depth3}, {self.depth4}"


class ZoneChannelNames:
    def __init__(self, zone: str, idx: int):
        self.zone_name = f"zone{idx}-{zone}".lower()
        self.stat_name = f"{self.zone_name}-stat"
        self.temp = f"{self.zone_name}-temp"
        self.set = f"{self.zone_name}-set"
        self.state = f"{self.zone_name}-state"

    def __repr__(self) -> str:
        return f"Channels: .temp: {self.temp}, .set: {self.set}, .state: {self.state}"


class TankChannelNames:
    def __init__(self, tank_name: str):
        self.depth1 = f"{tank_name}-depth1"
        self.depth2 = f"{tank_name}-depth2"
        self.depth3 = f"{tank_name}-depth3"
        self.depth4 = f"{tank_name}-depth4"


class H0N:
    # core actors
    atn = "a"
    scada = "s"
    home_alone = "h"
    primary_power_meter = "power-meter"

    # core power-metered nodes
    hp_odu = "hp-odu"
    hp_idu = "hp-idu"
    dist_pump = "dist-pump"
    primary_pump = "primary-pump"
    store_pump = "store-pump"

    # core temperatures
    dist_swt = "dist-swt"
    dist_rwt = "dist-rwt"
    hp_lwt = "hp-lwt"
    hp_ewt = "hp-ewt"
    buffer_hot_pipe = "buffer-hot-pipe"
    buffer_cold_pipe = "buffer-cold-pipe"
    store_hot_pipe = "store-hot-pipe"
    store_cold_pipe = "store-cold-pipe"
    oat = "oat"
    buffer = TankNodes("buffer")
    tank: Dict[int, TankNodes] = {}
    zone: Dict[str, ZoneName] = {}

    # core flow-metered nodes
    dist_flow = "dist-flow"
    primary_flow = "primary-flow"
    store_flow = "store-flow"

    hubitat = "hubitat"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        for i in range(total_store_tanks):
            self.tank[i + 1] = TankNodes(f"tank{i + 1}")
        for i in range(len(zone_list)):
            self.zone[zone_list[i]] = ZoneName(zone=zone_list[i], idx=i)


class H0Readers:
    analog_temp = "analog-temp"


class H0CN:
    # Power Channels
    hp_odu_pwr = f"{H0N.hp_odu}-pwr"
    hp_idu_pwr = f"{H0N.hp_idu}-pwr"
    dist_pump_pwr = f"{H0N.dist_pump}-pwr"
    primary_pump_pwr = f"{H0N.primary_pump}-pwr"
    store_pump_pwr = f"{H0N.store_pump}-pwr"

    # Temperature Channels
    dist_swt = H0N.dist_swt
    dist_rwt = H0N.dist_rwt
    hp_lwt = H0N.hp_lwt
    hp_ewt = H0N.hp_ewt
    store_hot_pipe = H0N.store_hot_pipe
    store_cold_pipe = H0N.store_cold_pipe
    buffer_hot_pipe = H0N.buffer_hot_pipe
    buffer_cold_pipe = H0N.buffer_cold_pipe
    oat = H0N.oat
    buffer = TankChannelNames("buffer")
    tank: Dict[int, TankChannelNames] = {}
    zone: Dict[int, ZoneChannelNames] = {}

    # Flow Channels
    dist_flow = H0N.dist_flow
    primary_flow = H0N.primary_flow
    store_flow = H0N.store_flow
    dist_flow_integrated = f"{H0N.dist_flow}-integrated"
    primary_flow_integrated = f"{H0N.primary_flow}-integrated"
    store_flow_integrated = f"{H0N.store_flow}-integrated"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        for i in range(total_store_tanks):
            self.tank[i + 1] = TankChannelNames(f"tank{i + 1}")
        for i in range(len(zone_list)):
            self.zone[i + 1] = ZoneChannelNames(zone=zone_list[i], idx=i + 1)

    def channel_stubs(self) -> Dict[str, ChannelStub]:
        d = {
            self.hp_odu_pwr: ChannelStub(
                Name=self.hp_odu_pwr,
                AboutNodeName=H0N.hp_odu,
                TelemetryName=TelemetryName.PowerW,
                InPowerMetering=True,
            ),
            self.hp_idu_pwr: ChannelStub(
                Name=self.hp_idu_pwr,
                AboutNodeName=H0N.hp_idu,
                TelemetryName=TelemetryName.PowerW,
                InPowerMetering=True,
            ),
            self.dist_pump_pwr: ChannelStub(
                Name=self.dist_pump_pwr,
                AboutNodeName=H0N.dist_pump,
                TelemetryName=TelemetryName.PowerW,
            ),
            self.primary_pump_pwr: ChannelStub(
                Name=self.primary_pump_pwr,
                AboutNodeName=H0N.primary_pump,
                TelemetryName=TelemetryName.PowerW,
            ),
            self.store_pump_pwr: ChannelStub(
                Name=self.store_pump_pwr,
                AboutNodeName=H0N.store_pump,
                TelemetryName=TelemetryName.PowerW,
            ),
            self.dist_swt: ChannelStub(
                Name=self.dist_swt,
                AboutNodeName=H0N.dist_swt,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.dist_rwt: ChannelStub(
                Name=self.dist_rwt,
                AboutNodeName=H0N.dist_rwt,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.hp_lwt: ChannelStub(
                Name=self.hp_lwt,
                AboutNodeName=H0N.hp_lwt,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.hp_ewt: ChannelStub(
                Name=self.hp_ewt,
                AboutNodeName=H0N.hp_ewt,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.store_hot_pipe: ChannelStub(
                Name=self.store_hot_pipe,
                AboutNodeName=H0N.store_hot_pipe,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.store_cold_pipe: ChannelStub(
                Name=self.store_cold_pipe,
                AboutNodeName=H0N.store_cold_pipe,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.buffer_hot_pipe: ChannelStub(
                Name=self.buffer_hot_pipe,
                AboutNodeName=H0N.buffer_hot_pipe,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.buffer_cold_pipe: ChannelStub(
                Name=self.buffer_cold_pipe,
                AboutNodeName=H0N.buffer_cold_pipe,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.oat: ChannelStub(
                Name=self.oat,
                AboutNodeName=H0N.oat,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.dist_flow: ChannelStub(
                Name=self.dist_flow,
                AboutNodeName=H0N.dist_flow,
                TelemetryName=TelemetryName.GpmTimes100,
            ),
            self.primary_flow: ChannelStub(
                Name=self.primary_flow,
                AboutNodeName=H0N.primary_flow,
                TelemetryName=TelemetryName.GpmTimes100,
            ),
            self.store_flow: ChannelStub(
                Name=self.store_flow,
                AboutNodeName=H0N.store_flow,
                TelemetryName=TelemetryName.GpmTimes100,
            ),
            self.dist_flow_integrated: ChannelStub(
                Name=self.dist_flow_integrated,
                AboutNodeName=H0N.dist_flow,
                TelemetryName=TelemetryName.GallonsTimes100,
            ),
            self.primary_flow_integrated: ChannelStub(
                Name=self.primary_flow_integrated,
                AboutNodeName=H0N.primary_flow,
                TelemetryName=TelemetryName.GallonsTimes100,
            ),
            self.store_flow_integrated: ChannelStub(
                Name=self.store_flow_integrated,
                AboutNodeName=H0N.store_flow,
                TelemetryName=TelemetryName.GallonsTimes100,
            ),
            self.buffer.depth1: ChannelStub(
                Name=self.buffer.depth1,
                AboutNodeName=H0N.buffer.depth1,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.buffer.depth2: ChannelStub(
                Name=self.buffer.depth2,
                AboutNodeName=H0N.buffer.depth2,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.buffer.depth3: ChannelStub(
                Name=self.buffer.depth3,
                AboutNodeName=H0N.buffer.depth3,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
            self.buffer.depth4: ChannelStub(
                Name=self.buffer.depth4,
                AboutNodeName=H0N.buffer.depth4,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            ),
        }
        for i in self.tank:
            d[self.tank[i].depth1] = ChannelStub(
                Name=self.tank[i].depth1,
                AboutNodeName=self.tank[i].depth1,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
            d[self.tank[i].depth2] = ChannelStub(
                Name=self.tank[i].depth2,
                AboutNodeName=self.tank[i].depth2,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
            d[self.tank[i].depth3] = ChannelStub(
                Name=self.tank[i].depth3,
                AboutNodeName=self.tank[i].depth3,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
            d[self.tank[i].depth4] = ChannelStub(
                Name=self.tank[i].depth4,
                AboutNodeName=self.tank[i].depth4,
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        for i in self.zone:
            d[self.zone[i].temp] = (
                ChannelStub(
                    Name=self.zone[i].temp,
                    AboutNodeName=self.zone[i].zone_name,
                    TelemetryName=TelemetryName.AirTempFTimes1000,
                ),
            )
            d[self.zone[i].set] = (
                ChannelStub(
                    Name=self.zone[i].temp,
                    AboutNodeName=self.zone[i].stat_name,
                    TelemetryName=TelemetryName.AirTempFTimes1000,
                ),
            )
            d[self.zone[i].set] = (
                ChannelStub(
                    Name=self.zone[i].state,
                    AboutNodeName=self.zone[i].stat_name,
                    TelemetryName=TelemetryName.ThermostatState,
                ),
            )
