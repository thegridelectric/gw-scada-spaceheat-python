import importlib.util
import math
import time
from enum import Enum
from typing import Dict, List

from actors2.config import ScadaSettings
from drivers.driver_result import DriverResult
from result import Err, Ok, Result

DRIVER_IS_REAL = True
for module_name in [
    "board",
    "busio",
    "adafruit_ads1x15",
    "adafruit_ads1x15.ads1115",
    "adafruit_ads1x15.analog_in",
]:
    found = importlib.util.find_spec(module_name)
    if found is None:
        DRIVER_IS_REAL = False
        break

DEFAULT_BAD_VALUE = -5


from data_classes.components.multipurpose_sensor_component import \
    MultipurposeSensorComponent
from drivers.exceptions import DriverWarning
from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver, TelemetrySpec)
from schema.enums import TelemetryName
from schema.enums.make_model.make_model_map import MakeModel


class TSnap1WrongTelemetryList(DriverWarning):
    ...


class TSnap1BadChannelList(DriverWarning):
    ...


class TSnap1NoI2cBus(DriverWarning):
    ...


class TSnapI2cAddressMissing(DriverWarning):
    ...


class TSnap1ComponentMisconfigured(DriverWarning):
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

# if DRIVER_IS_REAL:
#     # noinspection PyUnresolvedReferences
#     # noinspection PyUnresolvedReferences
# import adafruit_ads1x15.ads1115 as ADS
# import board
#
# # noinspection PyUnresolvedReferences
# import busio
#
# # noinspection PyUnresolvedReferences
# from adafruit_ads1x15.analog_in import AnalogIn


class GridworksTsnap1_MultipurposeSensorDriver(MultipurposeSensorDriver):
    ADS_1_I2C_ADDRESS = 0x48
    ADS_2_I2C_ADDRESS = 0x49
    ADS_3_I2C_ADDRESS = 0x4B
    # gives a range up to +/- 6.144V
    ADS_GAIN = 0.6666666666666666

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

    def try_connect(self, first_time: bool = False) -> Result[DriverResult, Exception]:

        if set(self.telemetry_name_list) != {TelemetryName.WATER_TEMP_C_TIMES1000}:
            return Err(TSnap1WrongTelemetryList())

        # Channel List needs to be a subset of [1, .., 12]
        readable_channel_list = list(filter(lambda x: 1 <= x <= 12, self.channel_list))
        if not set(self.channel_list) == set(readable_channel_list):
            return Err(TSnap1BadChannelList())

        # try:
        #     self.i2c = busio.I2C(board.SCL, board.SDA)
        # except:
        #     return Err(TSnap1NoI2cBus())
        #
        # self.ads = {}
        # try:
        #     self.ads[0] = ADS.ADS1115(address=self.ADS_1_I2C_ADDRESS, i2c=self.i2c)
        #     self.ads[0].gain = self.ADS_GAIN
        # except:
        #     return Err(TSnapI2cAddressMissing())
        # try:
        #     self.ads[1] = ADS.ADS1115(address=self.ADS_2_I2C_ADDRESS, i2c=self.i2c)
        #     self.ads[1].gain = self.ADS_GAIN
        # except:
        #     return Err(TSnapI2cAddressMissing())
        # try:
        #     self.ads[2] = ADS.ADS1115(address=self.ADS_3_I2C_ADDRESS, i2c=self.i2c)
        #     self.ads[2].gain = self.ADS_GAIN
        # except:
        #     return Err(TSnapI2cAddressMissing())
        return Ok(DriverResult(True))

    def start(self) -> Result[DriverResult[bool], Exception]:
        return self.try_connect(first_time=True)

    def read_telemetry_values(
        self, channel_telemetry_list: List[TelemetrySpec]
    ) -> Result[DriverResult[Dict[TelemetrySpec, int]], Exception]:
        result: Dict[TelemetrySpec, int] = {}

        for ts in channel_telemetry_list:
            # i = int(ts.ChannelIdx / 4)
            # j = (ts.ChannelIdx - 1) % 4
            # if j == 0:
            #     channel = AnalogIn(self.ads[i], ADS.P0)
            # elif j == 1:
            #     channel = AnalogIn(self.ads[i], ADS.P1)
            # elif j == 2:
            #     channel = AnalogIn(self.ads[i], ADS.P2)
            # else:
            #     channel = AnalogIn(self.ads[i], ADS.P3)
            #
            # voltage = channel.voltage
            voltage = 0.5 + 4.5 * ts.ChannelIdx / 12
            temp_c = self.thermistor_temp_c_beta_formula(voltage)
            if not ts.Type == TelemetryName.WATER_TEMP_C_TIMES1000:
                return Err(TSnap1ComponentMisconfigured())
            result[ts] = int(temp_c * 1000)

        return Ok(DriverResult(result))

    def thermistor_temp_c_beta_formula(self, voltage: float) -> float:
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


# else:
#
#     class GridworksTsnap1_MultipurposeSensorDriver(MultipurposeSensorDriver):
#         def __init__(
#                 self, component: MultipurposeSensorComponent, settings: ScadaSettings
#         ):
#             """
#             GridWorks TSnap1 has 12 terminal screwblocks, channels 1-12, that expect analog NTC
#             Thermistors with R0= 10 kOhhms. These go to 3 4-channel Ads 1115 i2c devices:
#             Ads1: channels 1-4
#             Ads2: channels 5-8
#             Ads3: channels 9-12
#
#             See https://drive.google.com/drive/u/0/folders/1xmUr6kwHAQ2DW8I5GsiIQHHLGnM2ybX- for more
#             TSNap channel information
#
#             See https://drive.google.com/drive/u/0/folders/1KySP9BqT8F-sH8fgEvb9O3x_CTVAt71h for
#             the Texas Instrument ADS1115 datasheet
#             """
#             super(GridworksTsnap1_MultipurposeSensorDriver, self).__init__(
#                 component=component, settings=settings
#             )
#             self.thingy = 1
#         def read_telemetry_values(
#             self, channel_telemetry_list: List[TelemetrySpec]
#         ) -> Result[DriverResult[Dict[TelemetrySpec, int]], Exception]:
#             raise NotImplementedError
