from typing import Dict, List
DEFAULT_ANALOG_READER = "analog-temp"
from gwproto.data_classes.telemetry_tuple import ChannelStub
from gwproto.enums import TelemetryName
class ZoneName:
    def __init__(self, zone: str, idx: int):
        zone_name = f"zone{idx + 1}-{zone}".lower()
        self.zone_name = zone_name
        self.stat = f"{zone_name}-stat"


class TankNodes:
    def __init__(self, tank_name: str):
        self.reader = tank_name
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

    # core temperatures
    buffer_cold_pipe = "buffer-cold-pipe"
    buffer_hot_pipe = "buffer-hot-pipe"
    buffer = TankNodes("buffer")
    dist_rwt = "dist-rwt"
    dist_swt = "dist-swt"
    hp_ewt = "hp-ewt"
    hp_lwt = "hp-lwt"
    oat = "oat"
    store_cold_pipe = "store-cold-pipe"
    store_hot_pipe = "store-hot-pipe"

    # core power-metered nodes
    hp_idu = "hp-idu"
    hp_odu = "hp-odu"
    dist_pump = "dist-pump"
    primary_pump = "primary-pump"
    store_pump = "store-pump"

    # core flow-metered nodes
    dist_flow = "dist-flow"
    primary_flow = "primary-flow"
    store_flow = "store-flow"

    hubitat = "hubitat"

    zone: Dict[str, ZoneName] = {}
    tank: Dict[int, TankNodes] = {}

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        for i in range(total_store_tanks):
            self.tank[i + 1] = TankNodes(f"tank{i + 1}")
        for i in range(len(zone_list)):
            self.zone[zone_list[i]] = ZoneName(zone=zone_list[i], idx=i)


class H0CN:
    hp_odu_pwr = "hp-odu-pwr"
    hp_idu_pwr = "hp-idu-pwr"
    store_pump_pwr = "store-pump-pwr"


ChannelStubByName = {
    H0CN.hp_odu_pwr: ChannelStub(
        Name=H0CN.hp_odu_pwr,
        AboutNodeName=H0N.hp_odu,
        CapturedByNodeName=H0N.primary_power_meter,
        TelemetryName=TelemetryName.PowerW,
        InPowerMetering=True,
    ),
    H0CN.hp_idu_pwr: ChannelStub(
        Name=H0CN.hp_idu_pwr,
        AboutNodeName=H0N.hp_idu,
        CapturedByNodeName=H0N.primary_power_meter,
        TelemetryName=TelemetryName.PowerW,
        InPowerMetering=True,
    ),
    H0CN.store_pump_pwr: ChannelStub(
        Name=H0CN.store_pump_pwr,
        AboutNodeName=H0N.store_pump,
        CapturedByNodeName=H0N.primary_power_meter,
        TelemetryName=TelemetryName.PowerW
    ),

}