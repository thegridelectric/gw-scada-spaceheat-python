import logging
import time
from enum import auto
from enum import StrEnum
from typing import Any
from typing import Deque
from typing import Mapping
from typing import Sequence

from cryptography.utils import cached_property

from typing import Optional

from gwproto.data_classes.data_channel import DataChannel
from gwproto.enums import TelemetryName
from gwproto.types import SingleReading
from gwproto.types import SnapshotSpaceheat
from pydantic import BaseModel

PUMP_OFF_THRESHOLD = 2


class BaseReading(BaseModel):
    string: str = ""

    def __str__(self):
        return self.string

    def __bool__(self) -> bool:
        return False

class MissingReading(BaseReading): ...

class Reading(BaseReading):
    raw: int
    converted: float | int
    report_time_unix_ms: int
    idx: int

    def __bool__(self) -> bool:
        return True

DEFAULT_MISSING_STRING = " --- "
DEFAULT_FORMAT_STRING = "{converted:3.1f}"

class DisplayChannel:
    name: str
    telemetry_name: TelemetryName = TelemetryName.Unknown
    format_string: str
    exists: bool = False
    missing_string: str
    raise_errors: bool = False
    logger: logging.Logger | logging.LoggerAdapter
    last_reading: Reading | MissingReading

    def __init__(
        self,
        name: str,
        channels: dict[str, DataChannel],
        *,
        format_string: str = DEFAULT_FORMAT_STRING,
        missing_string: str = DEFAULT_MISSING_STRING,
        raise_errors: bool = False,
        logger: Optional[logging.Logger | logging.LoggerAdapter] = None
    ) -> None:
        self.name = name
        channel = channels.get(name)
        self.exists = channel is not None
        if self.exists:
            self.telemetry_name = channel.TelemetryName
        self.format_string = format_string
        self.missing_string = missing_string
        self.raise_errors = raise_errors
        if logger is None:
            logger = logging.Logger(__file__)
        self.logger = logger
        self.last_reading = MissingReading(string=self.missing_string)

    def __bool__(self) -> bool:
        return self.exists

    def __str__(self) -> str:
        return str(self.last_reading)

    def convert(self, raw:int) -> float | int:  # noqa
        return float(raw)

    def format(self, converted: float | int) -> str:
        return self.format_string.format(converted=converted)

    def read_snapshot(self, snap: SnapshotSpaceheat) -> Reading | MissingReading:
        self.last_reading = MissingReading(string=self.missing_string)
        if self.exists:
            try:
                for i, reading in enumerate(snap.LatestReadingList):
                    if reading.ChannelName == self.name:
                        raw = snap.LatestReadingList[i].Value
                        converted = self.convert(raw)
                        self.last_reading = Reading(
                            string=self.format(converted),
                            raw=raw,
                            converted=converted,
                            report_time_unix_ms=snap.LatestReadingList[i].ScadaReadTimeUnixMs,
                            idx=i,
                        )
                        break
            except Exception as e:  # noqa
                self.logger.error(f"ERROR in channel <{self.name}> read")
                self.logger.exception(e)
                if self.raise_errors:
                    raise
        return self.last_reading

class TemperatureChannel(DisplayChannel):
    celsius_data: bool
    fahrenheit_display: bool

    def __init__(
        self,
        name: str,
        channels: dict[str, DataChannel],
        *,
        celcius_data: bool = True,
        fahrenheit_display: bool = True,
        missing_string: str = DEFAULT_MISSING_STRING,
        raise_errors: bool = False,
        logger: Optional[logging.Logger | logging.LoggerAdapter] = None
    ) -> None:
        self.fahrenheit_display = fahrenheit_display
        self.celcius_data = celcius_data
        format_string = "{converted:3.1f}\u00b0"
        if self.fahrenheit_display:
            format_string += "F"
        else:
            format_string += "C"
        super().__init__(
            name=name,
            channels=channels,
            format_string=format_string,
            missing_string=missing_string,
            raise_errors=raise_errors,
            logger=logger,
        )
        if self.exists:
            if self.celcius_data:
                valid_telemtery_names = TelemetryName.AirTempCTimes1000, TelemetryName.WaterTempCTimes1000
            else:
                valid_telemtery_names = TelemetryName.AirTempFTimes1000, TelemetryName.WaterTempFTimes1000
            if self.telemetry_name not in valid_telemtery_names:
                raise ValueError(
                    f"ERROR. Temperature channel {self.name} expects data in "
                    f"{valid_telemtery_names} "
                    f"but found {self.telemetry_name} in hardware layout"
                )

    def convert(self, raw: int) -> float | int:
        scaled = raw / 1000
        if self.celcius_data and self.fahrenheit_display:
            return 9 / 5 * scaled + 32
        elif not self.celcius_data and not self.fahrenheit_display:
            return (scaled - 32) * 5 / 9
        return scaled

class PowerChannel(DisplayChannel):
    kW: bool = True

    def __init__(self, *args, **kwargs) -> None:
        self.kW = kwargs.pop('kW', True)
        super().__init__(*args, **kwargs)
        if self.exists and self.telemetry_name != TelemetryName.PowerW:
            raise ValueError(
                f"ERROR. Power channel {self.name} expects telemetry "
                f"{TelemetryName.PowerW}. Got {self.telemetry_name}"
            )

    def convert(self, raw: int) -> float:
        raw = float(raw)
        if self.kW:
            raw /= 1000
        return round(raw, 2)

class PumpPowerChannel(PowerChannel):

    def __init__(self, *args, **kwargs) -> None:
        kwargs["kW"] = kwargs.get("kW", False)
        kwargs["missing_string"] = kwargs.get("missing_string", "---")
        super().__init__(*args, **kwargs)

    def format(self, converted: float | int) -> str:
        if converted < PUMP_OFF_THRESHOLD:
            return "OFF"
        return f"{round(converted, 2)}"

class UnusedReading(SingleReading):
    Telemetry: TelemetryName

class FlowChannel(DisplayChannel):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.exists and self.telemetry_name != TelemetryName.GpmTimes100:
            raise ValueError(
                f"ERROR. Flow channel {self.name} expects telemetry "
                f"{TelemetryName.GpmTimes100}. Got {self.telemetry_name}"
            )


class ReadMixin:
    def read_snapshot(self, snap: SnapshotSpaceheat, channels: dict[str, DataChannel]) -> list[UnusedReading]:
        """Read all existing child channels, update any ReadMixin children,
        return indices of any readings in the snapshot not read by a configured
        channel.

        This function itself is not meant to be called recursively.
        """
        for channel in self.channels:
            channel.read_snapshot(snap)
        self.update()
        return self.collect_unused_readings(snap, channels)

    def collect_unused_readings(self, snap: SnapshotSpaceheat, data_channels: dict[str, DataChannel]) -> list[UnusedReading]:
        used_indices = {channel.last_reading.idx for channel in self.channels if channel.last_reading}
        unused_readings = []
        for reading_idx in range(len(snap.LatestReadingList)):
            if reading_idx not in used_indices:
                unused_reading = snap.LatestReadingList[reading_idx]
                unused_readings.append(
                    UnusedReading(
                        ChannelName=unused_reading.ChannelName,
                        Value=unused_reading.Value,
                        ScadaReadTimeUnixMs=unused_reading.ScadaReadTimeUnixMs,
                        Telemetry=data_channels.get(unused_reading.ChannelName).TelemetryName
                    )
                )
        return unused_readings

    def update_self(self) -> None:
        """Overide with any extra code that must be called after ReadSnapshot"""

    def update_children(self) -> None:
        children = []
        for member in self.__dict__.values():
            if isinstance(member, ReadMixin):
                children.append(member)
            elif isinstance(member, Mapping) and member:
                for submember in member.values():
                    if isinstance(submember, ReadMixin):
                        children.append(submember)
            elif isinstance(member, (tuple, list)) and member:
                for submember in member:
                    if isinstance(submember, ReadMixin):
                        children.append(submember)
        for child in children:
            child.update()

    def update(self):
        self.update_self()
        self.update_children()

    def collect_channels(self, members: Optional[Sequence[Any]] = None) -> list[DisplayChannel]:
        collected_channels = []
        if members is None:
            members = self.__dict__.values()
        for member in members:
            if isinstance(member, DisplayChannel):
                collected_channels.append(member)
            elif isinstance(member, ReadMixin):
                collected_channels.extend(member.collect_channels())
            elif isinstance(member, Mapping) and member:
                collected_channels.extend(self.collect_channels(list(member.values())))
            elif isinstance(member, (tuple, list)) and member:
                collected_channels.extend(self.collect_channels(member))
        return collected_channels

    @cached_property
    def channels(self) -> list[DisplayChannel]:
        return self.collect_channels()

def enqueue_fifo_q(element: Any, fifo_q: Deque[Any], max_length: int = 10) -> None:
    """
    Enqueues an element into a FIFO queue represented by a deque object.

    Args:
        element (HackHpStateCapture): The element to be enqueued.
        fifo_q (Deque[HackHpStateCapture]): The FIFO queue represented by a deque object.
        max_length (int, optional): The maximum length of the FIFO queue. Defaults to 10.

    Returns:
        None
    """
    if len(fifo_q) >= max_length:
        fifo_q.pop()  # Remove the oldest element if queue length is equal to max_length
    fifo_q.appendleft(element)  # Add the new element at the beginning

class PumpPowerState(StrEnum):
    NoFlow = auto()
    Flow = auto()

class PumpPowerChannels(ReadMixin):
    primary: PumpPowerChannel
    store: PumpPowerChannel
    dist: PumpPowerChannel
    boiler: PumpPowerChannel
    dist_pump_pwr_state_q: Deque[tuple[PumpPowerState, int, int]]
    dist_pump_pwr_state: PumpPowerState

    def __init__(self, channels: dict[str, DataChannel]) -> None:
        self.primary = PumpPowerChannel("primary-pump-pwr", channels)
        self.store = PumpPowerChannel("store-pump-pwr", channels)
        self.dist = PumpPowerChannel("dist-pump-pwr", channels)
        self.boiler = PumpPowerChannel("oil-boiler-pwr", channels)
        self.dist_pump_pwr_state_q = Deque[tuple[PumpPowerState, int, int]](maxlen=10)
        self.dist_pump_pwr_state = PumpPowerState.NoFlow

    def update(self):
        now = int(time.time())
        if self.dist.last_reading:
            if self.dist_pump_pwr_state == PumpPowerState.NoFlow:
                if self.dist.last_reading.converted > PUMP_OFF_THRESHOLD:
                    self.dist_pump_pwr_state = PumpPowerState.Flow
                    tt = [PumpPowerState.Flow, self.dist.last_reading.converted, now]
                    enqueue_fifo_q(tt, self.dist_pump_pwr_state_q)
            elif self.dist_pump_pwr_state == PumpPowerState.Flow:
                if self.dist.last_reading.converted < PUMP_OFF_THRESHOLD:
                    self.dist_pump_pwr_state = PumpPowerState.NoFlow
                    tt = [PumpPowerState.NoFlow, self.dist.last_reading.converted, now]
                    enqueue_fifo_q(tt, self.dist_pump_pwr_state_q)


class PowerChannels(ReadMixin):
    hp_indoor: PowerChannel
    hp_outdoor: PowerChannel
    pumps: PumpPowerChannels

    def __init__(self, channels: dict[str, DataChannel]) -> None:
        self.hp_indoor = PowerChannel("hp-idu-pwr", channels)
        self.hp_outdoor = PowerChannel("hp-odu-pwr", channels)
        self.hp_total = MissingReading()
        self.pumps = PumpPowerChannels(channels)

class Thermostat(ReadMixin):
    name: str
    set_point: TemperatureChannel
    temperature: TemperatureChannel

    def __init__(
        self, name: str,
        channels: dict[str, DataChannel],
        *,
        celcius_data: bool = True,
        fahrenheit_display: bool = True,
        missing_string: str = DEFAULT_MISSING_STRING,
        raise_errors: bool = False,
        logger: Optional[logging.Logger | logging.LoggerAdapter] = None
    ) -> None:
        self.name = name
        self.set_point = TemperatureChannel(
            self.name + "-set",
            channels,
            celcius_data=celcius_data,
            fahrenheit_display=fahrenheit_display,
            missing_string=missing_string,
            raise_errors=raise_errors,
            logger=logger
        )
        self.temperature = TemperatureChannel(
            self.name + "-temp",
            channels,
            celcius_data = celcius_data,
            fahrenheit_display = fahrenheit_display,
            missing_string = missing_string,
            raise_errors = raise_errors,
            logger = logger,
            )

class HoneywellThermostat(Thermostat):
    state: DisplayChannel

    def __init__(
        self, name:
        str, channels: dict[str, DataChannel],
        *,
        fahrenheit_display: bool = True,
        missing_string: str = DEFAULT_MISSING_STRING,
        raise_errors: bool = False,
        logger: Optional[logging.Logger | logging.LoggerAdapter] = None

    ) -> None:
        super().__init__(
            name,
            channels,
            celcius_data=False,
            fahrenheit_display=fahrenheit_display,
            missing_string=missing_string,
            raise_errors=raise_errors,
            logger=logger,
        )
        self.state = DisplayChannel(
            self.name + "-state",
            channels,
            missing_string=missing_string,
            raise_errors=raise_errors,
            logger=logger,
        )

class Tank(ReadMixin):
    name: str
    depth1: TemperatureChannel
    depth2: TemperatureChannel
    depth3: TemperatureChannel
    depth4: TemperatureChannel
    is_buffer: bool

    def __init__(self, tank_name: str, channels: dict[str, DataChannel], *, is_buffer: bool = False) -> None:
        self.name = tank_name
        self.depth1 = TemperatureChannel(self.name + "-depth1", channels)
        self.depth2 = TemperatureChannel(self.name + "-depth2", channels)
        self.depth3 = TemperatureChannel(self.name + "-depth3", channels)
        self.depth4 = TemperatureChannel(self.name + "-depth4", channels)
        self.is_buffer = is_buffer


class Tanks(ReadMixin):
    buffer: Tank
    store: list[Tank]

    def __init__(self, num_tanks: int, channels: dict[str, DataChannel]) -> None:
        self.buffer = Tank("buffer", channels, is_buffer=True)
        self.store = [
            Tank(f"tank{tank_idx}", channels)
            for tank_idx in range(1, num_tanks + 1)
        ]

class Temperatures(ReadMixin):
    tanks: Tanks
    thermostats: list[HoneywellThermostat]
    dist_swt: TemperatureChannel   # = "dist-swt"
    dist_rwt: TemperatureChannel   # = "dist-rwt"
    hp_lwt: TemperatureChannel   # = "hp-lwt"
    hp_ewt: TemperatureChannel   # = "hp-ewt"
    buffer_hot_pipe: TemperatureChannel   # = "buffer-hot-pipe"
    buffer_cold_pipe: TemperatureChannel   # = "buffer-cold-pipe"
    store_hot_pipe: TemperatureChannel   # = "store-hot-pipe"
    store_cold_pipe: TemperatureChannel   # = "store-cold-pipe"
    oat: TemperatureChannel   # = "oat"

    def __init__(
        self,
        num_tanks: int,
        thermostat_names: list[str],
        channels: dict[str, DataChannel]
    ) -> None:
        self.tanks = Tanks(num_tanks, channels)
        self.thermostats = [
            HoneywellThermostat(
                f"zone{i+1}-{thermostat_name}", channels
            ) for i, thermostat_name in enumerate(thermostat_names)
        ]
        self.dist_swt = TemperatureChannel("dist-swt", channels)
        self.dist_rwt = TemperatureChannel("dist-rwt", channels)
        self.hp_lwt = TemperatureChannel("hp-lwt", channels)
        self.hp_ewt = TemperatureChannel("hp-ewt", channels)
        self.buffer_hot_pipe = TemperatureChannel("buffer-hot-pipe", channels)
        self.buffer_cold_pipe = TemperatureChannel("buffer-cold-pipe", channels)
        self.store_hot_pipe = TemperatureChannel("store-hot-pipe", channels)
        self.store_cold_pipe = TemperatureChannel("store-cold-pipe", channels)
        self.oat = TemperatureChannel("oat", channels)

class FlowChannels(ReadMixin):
    dist_flow: FlowChannel
    primary_flow: FlowChannel
    store_flow: FlowChannel

    def __init__(self, channels: dict[str, DataChannel]) -> None:
        self.dist_flow = FlowChannel("dist-flow", channels)
        self.primary_flow = FlowChannel("primary-flow", channels)
        self.store_flow = FlowChannel("store-flow", channels)

class Channels(ReadMixin):
    power: PowerChannels
    temperatures: Temperatures
    flows: FlowChannels
    last_unused_readings: list[UnusedReading]

    def __init__(
        self,
        channels: dict[str, DataChannel],
        thermostat_names: list[str],
    ) -> None:
        self.power = PowerChannels(channels)
        self.temperatures = Temperatures(num_tanks=3, thermostat_names=thermostat_names, channels=channels)
        self.flows = FlowChannels(channels)
        self.last_unused_readings = []

    def read_snapshot(self, snap: SnapshotSpaceheat, channels: dict[str, DataChannel]) -> list[UnusedReading]:
        self.last_unused_readings = super().read_snapshot(snap, channels)
        return self.last_unused_readings
