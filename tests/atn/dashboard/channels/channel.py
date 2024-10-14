import logging

from typing import Optional

from gwproto.data_classes.data_channel import DataChannel
from gwproto.enums import TelemetryName
from gwproto.types import SingleReading
from gwproto.types import SnapshotSpaceheat

from tests.atn.dashboard.channels.reading import MissingReading
from tests.atn.dashboard.channels.reading import Reading

PUMP_OFF_THRESHOLD = 2

DEFAULT_MISSING_STRING = "  ---  "
DEFAULT_FORMAT_STRING = "{converted:3.1f}"

class DisplayChannel:
    name: str
    telemetry_name: TelemetryName = TelemetryName.Unknown
    format_string: str
    exists: bool = False
    missing_string: str
    raise_errors: bool = False
    logger: logging.Logger | logging.LoggerAdapter
    reading: Reading | MissingReading

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
        self.reading = MissingReading(string=self.missing_string)

    def __bool__(self) -> bool:
        return self.exists

    def __str__(self) -> str:
        return str(self.reading)

    @property
    def raw(self) -> Optional[int]:
        if self.exists and self.reading:
            return self.reading.raw
        return None

    @property
    def converted(self) -> Optional[float | int]:
        if self.exists and self.reading:
            return self.reading.converted
        return None

    def convert(self, raw:int) -> float | int:  # noqa
        return float(raw)

    def format(self, converted: float | int) -> str:
        return self.format_string.format(converted=converted)

    def read_snapshot(self, snap: SnapshotSpaceheat) -> Reading | MissingReading:
        self.reading = MissingReading(string=self.missing_string)
        if self.exists:
            try:
                for i, reading in enumerate(snap.LatestReadingList):
                    if reading.ChannelName == self.name:
                        raw = snap.LatestReadingList[i].Value
                        converted = self.convert(raw)
                        self.reading = Reading(
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
        return self.reading

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
        format_string = "{converted:5.1f}\u00b0"
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
