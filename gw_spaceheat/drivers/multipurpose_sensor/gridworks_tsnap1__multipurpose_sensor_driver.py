import math
import sys
from enum import Enum
from typing import Dict, List

from result import Err, Ok, Result

# noinspection PyUnresolvedReferences
import adafruit_ads1x15.ads1115 as ADS

# noinspection PyUnresolvedReferences
import board

# noinspection PyUnresolvedReferences
import busio

# noinspection PyUnresolvedReferences
from adafruit_ads1x15.analog_in import AnalogIn


from actors2.config import ScadaSettings
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from drivers.driver_result import DriverResult
from drivers.exceptions import DriverError
from drivers.exceptions import DriverWarning
from drivers.multipurpose_sensor.multipurpose_sensor_driver import MultipurposeSensorDriver
from drivers.multipurpose_sensor.multipurpose_sensor_driver import TelemetrySpec
from schema.enums import TelemetryName
from schema.enums.make_model.make_model_map import MakeModel

DEFAULT_BAD_VALUE = -5


class SetCompareError(DriverError):
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
        s += (
            f"\n\texp: {sorted(self.expected)}"
            f"\n\tgot: {sorted(self.got)}"
        )
        return s


class TSnap1WrongTelemetryList(SetCompareError):
    ...


class TSnap1BadChannelList(SetCompareError):
    ...


class TSnap1NoI2cBus(DriverError):
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
        s += f"   address:{self.address}"
        return s


class TSnap1ComponentMisconfigured(DriverError):
    ...


class I2CErrorEnum(Enum):
    NO_ADDRESS_ERROR = -100000
    READ_ERROR = -200000


PI_VOLTAGE = 5
# 298 Kelvin is 25 Celcius
THERMISTOR_T0_DEGREES_KELVIN = 298
# NTC THermistors are 10 kOhms at 25 deg C
THERMISTOR_R0_OHMS = 10000
# NTC Thermistors have a "rated beta" on their data sheet
THERMISTOR_BETA = 3977
# Then, there is our pull-up resistor
VOLTAGE_DIVIDER_R_OHMS = 8200

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
        if set(self.telemetry_name_list) != {TelemetryName.WATER_TEMP_C_TIMES1000}:
            return Err(TSnap1WrongTelemetryList(
                {TelemetryName.WATER_TEMP_C_TIMES1000},
                self.telemetry_name_list
            ))

        # Channel List needs to be a subset of [1, .., 12]
        readable_channel_list = list(filter(lambda x: 1 <= x <= 12, self.channel_list))
        if not set(self.channel_list) == set(readable_channel_list):
            return Err(TSnap1BadChannelList(readable_channel_list, self.channel_list))

        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
        except BaseException as e:
            return Err(TSnap1NoI2cBus(str(board.SCL), str(board.SDA), msg=str(e)).with_traceback(sys.exc_info()[2]))

        self.ads = {}
        start_result = DriverResult(True)
        for idx, addr in [
            (0, self.ADS_1_I2C_ADDRESS),
            (1, self.ADS_2_I2C_ADDRESS),
            (2, self.ADS_3_I2C_ADDRESS),
        ]:
            try:
                self.ads[idx] = ADS.ADS1115(address=addr, i2c=self.i2c)
                self.ads[idx].gain = self.ADS_GAIN
            except ValueError as e:
                start_result.warnings.append(
                    TSnapI2cAddressMissing(addr, msg=str(e)).with_traceback(sys.exc_info()[2])
                )
        return Ok(start_result)

    def read_telemetry_values(
        self, channel_telemetry_list: List[TelemetrySpec]
    ) -> Result[DriverResult[Dict[TelemetrySpec, int]], Exception]:
        result: Dict[TelemetrySpec, int] = {}
        for ts in channel_telemetry_list:
            i = int(ts.ChannelIdx / 4)
            if i in self.ads:
                j = (ts.ChannelIdx - 1) % 4
                if j == 0:
                    channel = AnalogIn(self.ads[i], ADS.P0)
                elif j == 1:
                    channel = AnalogIn(self.ads[i], ADS.P1)
                elif j == 2:
                    channel = AnalogIn(self.ads[i], ADS.P2)
                else:
                    channel = AnalogIn(self.ads[i], ADS.P3)
                voltage = channel.voltage
                temp_c = self.thermistor_temp_c_beta_formula(voltage)
                if not ts.Type == TelemetryName.WATER_TEMP_C_TIMES1000:
                    return Err(TSnap1ComponentMisconfigured(str(ts)))
                result[ts] = int(temp_c * 1000)
        return Ok(DriverResult(result))

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

        # Calculate the resistance of the thermistor
        rt = rd * voltage / (PI_VOLTAGE - voltage)

        # Calculate the temperature in degrees Celsius. Note that 273 is
        # 0 degrees Celcius as measured in Kelvin.

        temp_c = 1 / ((1 / t0) + (math.log(rt / r0) / beta)) - 273

        return temp_c
