from gwproto.data_classes.components.multipurpose_sensor_component import (
    MultipurposeSensorComponent,
)
from enums import MakeModel, TelemetryName
from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
    TelemetrySpec,
)
from adafruit_ads1x15.analog_in import AnalogIn
import busio
import board
import adafruit_ads1x15.ads1115 as ADS
import math
import sys
from enum import Enum
from typing import Dict, List
from actors.config import ScadaSettings

from drivers.driver_result import DriverResult
from drivers.exceptions import DriverWarning

from result import Err, Ok, Result

DEFAULT_BAD_VALUE = -5

# noinspection PyUnresolvedReferences
import adafruit_ads1x15.ads1115 as ADS

# noinspection PyUnresolvedReferences
import board

# noinspection PyUnresolvedReferences
import busio

# noinspection PyUnresolvedReferences
from adafruit_ads1x15.analog_in import AnalogIn
from drivers.exceptions import DriverWarning
from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
    TelemetrySpec,
)
from enums import MakeModel, TelemetryName
from gwproto.data_classes.components.multipurpose_sensor_component import (
    MultipurposeSensorComponent,
)


class SetCompareWarning(DriverWarning):
    expected: set
    got: set

    def __init__(
        self,
        expected: set | list,
        got: set | list,
        msg: str = "",
    ):
        super().__init__(msg)
        self.expected = set(expected)
        self.got = set(got)

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += f"\n\texp: {sorted(self.expected)}" f"\n\tgot: {sorted(self.got)}"
        return s


class TSnap1WrongTelemetryList(SetCompareWarning):
    ...


class TSnap1BadChannelList(SetCompareWarning):
    ...


class TSnap1NoI2cBus(DriverWarning):
    SCL: str
    SDA: str

    def __init__(
        self,
        scl: str,
        sda: str,
        msg: str = "",
    ):
        super().__init__(msg)
        self.scl = scl
        self.sda = sda

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += f"   SCL:{self.scl}  SDA:{self.sda}"
        return s


class TSnapI2cAddressMissing(DriverWarning):
    address: int

    def __init__(
        self,
        address: int,
        msg: str = "",
    ):
        super().__init__(msg)
        self.address = address

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += f"   address:0x{self.address:02X}"
        return s


class TSnapI2cReadWarning(DriverWarning):
    idx: int
    address: int
    pin: int

    def __init__(
        self,
        idx: int,
        address: int,
        pin: int,
        msg: str = "",
    ):
        super().__init__(msg)
        self.idx = idx
        self.address = address
        self.pin = pin

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += f"   idx:{self.idx}  address:0x{self.address:02X}  pin:{self.pin}"
        return s


class TSnap1ComponentMisconfigured(DriverWarning):
    ...


class I2CErrorEnum(Enum):
    NO_ADDRESS_ERROR = -100000
    READ_ERROR = -200000


PI_VOLTAGE = 5.1
# 298 Kelvin is 25 Celcius
THERMISTOR_T0_DEGREES_KELVIN = 298
# NTC THermistors are 10 kOhms at 25 deg C
THERMISTOR_R0_OHMS = 10000
# NTC Thermistors have a "rated beta" on their data sheet
THERMISTOR_BETA = 3977
# Then, there is our pull-up resistor
VOLTAGE_DIVIDER_R_OHMS = 10000


class GridworksTsnap1_MultipurposeSensorDriver(MultipurposeSensorDriver):
    ADS_1_I2C_ADDRESS = 0x48
    ADS_2_I2C_ADDRESS = 0x49
    ADS_3_I2C_ADDRESS = 0x4B
    # gives a range up to +/- 6.144V
    ADS_GAIN = 0.6666666666666666

    ads: dict[int, ADS]
    i2c: busio.I2C

    def __init__(self, component: MultipurposeSensorComponent, settings: ScadaSettings):
        """
        GridWorks TSnap1 has 12 terminal screwblocks, channels 1-12, that expect analog NTC
        Thermistors with R0= 10 kOhhms. These go to 3 4-channel Ads 1115 i2c devices:
        Ads1: channels 1-4
        Ads2: channels 5-8
        Ads3: channels 9-12

        See https://drive.google.com/drive/u/0/folders/1xmUr6kwHAQ2DW8I5GsiIQHHLGnM2ybX- for more
        TSNap channel information

        See https://drive.google.com/drive/u/0/folders/1KySP9BqT8F-sH8fgEvb9O3x_CTVAt71h for
        the Texas Instrument ADS1115 datasheet
        """
        super(GridworksTsnap1_MultipurposeSensorDriver, self).__init__(
            component=component, settings=settings
        )
        models: List[MakeModel] = [
            MakeModel.GRIDWORKS__TSNAP1,
        ]
        if component.cac.make_model not in models:
            raise Exception(
                f"Expected make model in {models}, got {component.cac.make_model}"
            )
        self.channel_list = component.channel_list
        self.telemetry_name_list = component.cac.telemetry_name_list

    def start(self) -> Result[DriverResult[bool], Exception]:
        if set(self.telemetry_name_list) != {TelemetryName.WaterTempCTimes1000}:
            return Err(
                TSnap1WrongTelemetryList(
                    {TelemetryName.WaterTempCTimes1000}, self.telemetry_name_list
                )
            )

        # Channel List needs to be a subset of [1, .., 12]
        readable_channel_list = list(filter(lambda x: 1 <= x <= 12, self.channel_list))
        if not set(self.channel_list) == set(readable_channel_list):
            return Err(TSnap1BadChannelList(readable_channel_list, self.channel_list))

        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
        except BaseException as e:
            return Err(
                TSnap1NoI2cBus(
                    str(board.SCL), str(board.SDA), msg=str(e)
                ).with_traceback(sys.exc_info()[2])
            )

        driver_result = DriverResult(True)
        self.ads = {}
        for idx, addr in [
            (0, self.ADS_1_I2C_ADDRESS),
            (1, self.ADS_2_I2C_ADDRESS),
            (2, self.ADS_3_I2C_ADDRESS),
        ]:
            try:
                ads1115 = ADS.ADS1115(address=addr, i2c=self.i2c)
                ads1115.gain = self.ADS_GAIN
            except BaseException as e:
                driver_result.warnings.append(
                    TSnapI2cAddressMissing(addr, msg=str(e)).with_traceback(
                        sys.exc_info()[2]
                    )
                )
                continue
            self.ads[idx] = ads1115
        return Ok(driver_result)

    def read_voltage(
        self, ts: TelemetrySpec
    ) -> Result[DriverResult[float | None], Exception]:
        driver_result = DriverResult[float | None](None)
        i = int((ts.ChannelIdx - 1) / 4)
        if i in self.ads:
            pin = [ADS.P0, ADS.P1, ADS.P2, ADS.P3][(ts.ChannelIdx - 1) % 4]
            try:
                channel = AnalogIn(self.ads[i], pin)
                voltage = channel.voltage
            except OSError as e:
                driver_result.warnings.append(e)
                driver_result.warnings.append(
                    TSnapI2cReadWarning(
                        idx=i, address=self.ads[i].i2c_device.device_address, pin=pin
                    )
                )
            else:
                if voltage >= PI_VOLTAGE:
                    driver_result.warnings.append(
                        TSnapI2cReadWarning(
                            idx=i,
                            address=self.ads[i].i2c_device.device_address,
                            pin=pin,
                            msg=(
                                f"Invalid voltage:{voltage:.2f};  must be less than: {PI_VOLTAGE}"
                            ),
                        )
                    )
                else:
                    driver_result.value = voltage
        return Ok(driver_result)

    def read_telemetry_values(
        self, channel_telemetry_list: List[TelemetrySpec]
    ) -> Result[DriverResult[Dict[TelemetrySpec, int]], Exception]:
        for ts in channel_telemetry_list:
            if not ts.Type == TelemetryName.WaterTempCTimes1000:
                return Err(TSnap1ComponentMisconfigured(str(ts)))
        driver_result = DriverResult[Dict[TelemetrySpec, int]]({})
        for ts in channel_telemetry_list:
            read_voltage_result = self.read_voltage(ts)
            if read_voltage_result.is_ok():
                if read_voltage_result.value.warnings:
                    driver_result.warnings.extend(read_voltage_result.value.warnings)
                if read_voltage_result.value.value is not None:
                    temp_c = self.thermistor_temp_c_beta_formula(
                        read_voltage_result.value.value
                    )
                    driver_result.value[ts] = int(temp_c * 1000)
        return Ok(driver_result)

    @classmethod
    def thermistor_temp_c_beta_formula(cls, voltage: float) -> float:
        """We are using the beta formula instead of the Steinhart-Hart equation.
        Thermistor data sheets typically provide the three parameters needed
        for the beta formula (R0, beta, and T0) and do not provide the
        three parameters needed for the better beta function.
        "Under the best conditions, the beta formula is accurate to approximately
        +/- 1 C over the temperature range of 0 to 100C

        For more information go here:
        https://www.newport.com/medias/sys_master/images/images/hdb/hac/8797291479070/TN-STEIN-1-Thermistor-Constant-Conversions-Beta-to-Steinhart-Hart.pdf

        Args:
            voltage (float): The voltage measured between the thermistor and the
            voltage divider resistor

        Returns:
            float: The temperature getting measured by the thermistor in degrees Celcius
        """
        rd: int = int(VOLTAGE_DIVIDER_R_OHMS)
        r0: int = int(THERMISTOR_R0_OHMS)
        beta: int = int(THERMISTOR_BETA)
        t0: int = int(THERMISTOR_T0_DEGREES_KELVIN)
        if voltage >= PI_VOLTAGE:
            return I2CErrorEnum.READ_ERROR.value
        # Calculate the resistance of the thermistor
        rt = rd * voltage / (PI_VOLTAGE - voltage)

        # Calculate the temperature in degrees Celsius. Note that 273 is
        # 0 degrees Celcius as measured in Kelvin.

        temp_c = 1 / ((1 / t0) + (math.log(rt / r0) / beta)) - 273

        return temp_c
