from typing import List
import importlib.util
from enum import Enum
import math
from config import ScadaSettings
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
COMPONENT_I2C_ADDRESS = 0x48

PI_VOLTAGE = 5
# 298 Kelvin is 25 Celcius
THERMISTOR_T0_DEGREES_KELVIN = 298
# NTC THermistors are 10 kOhms at 25 deg C
THERMISTOR_R0_OHMS = 10000
# NTC Thermistors have a "rated beta" on their data sheet
THERMISTOR_BETA = 3977
# Then, there is our pull-up resistor
VOLTAGE_DIVIDER_R_OHMS = 8200


class I2CErrorEnum(Enum):
    NO_ADDRESS_ERROR = -100000
    READ_ERROR = -200000


if DRIVER_IS_REAL:
    # noinspection PyUnresolvedReferences
    import board
    # noinspection PyUnresolvedReferences
    import busio
    # noinspection PyUnresolvedReferences
    import adafruit_ads1x15.ads1115 as ADS
    # noinspection PyUnresolvedReferences
    from adafruit_ads1x15.analog_in import AnalogIn

    from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
    from data_classes.components.temp_sensor_component import TempSensorComponent
    from schema.enums.make_model.make_model_map import MakeModel

    class G1_NcdAds1115_Ntc10k(TempSensorDriver):
        def __init__(self, component: TempSensorComponent, settings: ScadaSettings):
            super(G1_NcdAds1115_Ntc10k, self).__init__(component=component, settings=settings)
            self.channel_idx = component.channel
            models: List[MakeModel] = [
                MakeModel.G1__NCD_ADS1115__TEWA_NTC_10K_A,
                MakeModel.G1__NCD_ADS1115__AMPH_NTC_10K_A,
            ]
            if component.cac.make_model not in models:
                raise Exception(f"Expected make model in {models}, got {component.cac.make_model}")
            if component.channel is None:
                raise Exception(f"Need a channel 0-3 from Ads1115 temp sensor!")
            if component.channel not in range(4):
                raise Exception(f"Channel {component.channel} must be 0,1,2 or 3!")
            try:
                self.i2c = busio.I2C(board.SCL, board.SDA)
            except:
                raise Exception("Error creating busio.I2C device!")

        def thermistor_temp_c_beta_formula(
            self,
            voltage: float) -> float:
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
    

        def read_telemetry_value(self) -> int:
            try:
                ads = ADS.ADS1115(address=COMPONENT_I2C_ADDRESS, i2c=self.i2c)
            except:
                self.logger.warning(f"Failed to detect i2c at address {COMPONENT_I2C_ADDRESS}")
                return I2CErrorEnum.NO_ADDRESS_ERROR.value
            if self.channel_idx == 0:
                channel = AnalogIn(ads, ADS.P0)
            elif self.channel_idx == 1:
                channel = AnalogIn(ads, ADS.P1)
            elif self.channel_idx == 2:
                channel = AnalogIn(ads, ADS.P2)
            elif self.channel_idx == 3:
                channel = AnalogIn(ads, ADS.P3)
            try:
                voltage = channel.voltage 
                temp_c = self.thermistor_temp_c_beta_formula(voltage)
            except:
                self.logger.warning(f"Read bad value for {COMPONENT_I2C_ADDRESS}, channel {self.channel_idx}")
                return I2CErrorEnum.READ_ERROR.value
            return int(temp_c * 1000)
else:
    from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver

    class G1_NcdAds1115_Ntc10k(TempSensorDriver):

        def read_telemetry_value(self) -> int:
            raise NotImplementedError
