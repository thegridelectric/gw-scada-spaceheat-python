from typing import List
import importlib.util
from enum import Enum

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
        
        def read_telemetry_value(self) -> int:
            try:
                ads = ADS.ADS1115(address=COMPONENT_I2C_ADDRESS, channel=self.i2c)
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
                value = channel.voltage
                # value = self.channel.value
            except:
                self.logger.warning(f"Read bad value for {COMPONENT_I2C_ADDRESS}, channel {self.channel_idx}")
                return I2CErrorEnum.READ_ERROR.value
            return int(value * 1000)
else:
    from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver

    class G1_NcdAds1115_Ntc10k(TempSensorDriver):

        def read_telemetry_value(self) -> int:
            raise NotImplementedError
