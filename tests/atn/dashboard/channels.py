import logging
from typing import Any
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
        if not self.exists:
            self.last_reading = MissingReading(string=self.missing_string)
        else:
            try:
                idx = None
                for i, reading in enumerate(snap.LatestReadingList):
                    if reading.ChannelName == self.name:
                        idx = i
                        break
                if idx is not None:
                    raw = snap.LatestReadingList[idx].Value
                    converted = self.convert(raw)
                    self.last_reading = Reading(
                        string=self.format(converted),
                        raw=raw,
                        converted=converted,
                        report_time_unix_ms=snap.LatestReadingList[idx].ScadaReadTimeUnixMs,
                        idx=idx,
                    )
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

class ReadMixin:
    def read_snapshot(self, snap: SnapshotSpaceheat, channels: dict[str, DataChannel]) -> list[UnusedReading]:
        for channel in self.channels:
            channel.read_snapshot(snap)
        return self.collect_unused_readings(snap, channels)

    def collect_unused_readings(self, snap: SnapshotSpaceheat, channels: dict[str, DataChannel]) -> list[UnusedReading]:
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
                        Telemetry=channels.get(unused_reading.ChannelName).TelemetryName
                    )
                )
        return unused_readings


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

class PumpPowerChannels(ReadMixin):
    primary: PumpPowerChannel
    store: PumpPowerChannel
    dist: PumpPowerChannel
    boiler: PumpPowerChannel

    def __init__(self, channels: dict[str, DataChannel]) -> None:
        self.primary = PumpPowerChannel("primary-pump-pwr", channels)
        self.store = PumpPowerChannel("store-pump-pwr", channels)
        self.dist = PumpPowerChannel("dist-pump-pwr", channels)
        self.boiler = PumpPowerChannel("oil-boiler-pwr", channels)


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


class Channels(ReadMixin):
    power: PowerChannels
    thermostats: list[HoneywellThermostat]
    tanks: Tanks
    last_unused_readings: list[UnusedReading]

    def __init__(
        self,
        channels: dict[str, DataChannel],
        thermostat_names: Optional[list[str]] = None,
        tanks: Optional[Tanks] = None
    ) -> None:
        self.power = PowerChannels(channels)

        if thermostat_names is None:
            self.thermostats = []
        else:
            self.thermostats = [
                HoneywellThermostat(
                    f"zone{i+1}-{thermostat_name}", channels
                ) for i, thermostat_name in enumerate(thermostat_names)
            ]
        if tanks is None:
            tanks = Tanks(3, channels)
        self.tanks = tanks
        self.last_unused_readings = []

    def read_snapshot(self, snap: SnapshotSpaceheat, channels: dict[str, DataChannel]) -> list[UnusedReading]:
        self.last_unused_readings = super().read_snapshot(snap, channels)
        return self.last_unused_readings
