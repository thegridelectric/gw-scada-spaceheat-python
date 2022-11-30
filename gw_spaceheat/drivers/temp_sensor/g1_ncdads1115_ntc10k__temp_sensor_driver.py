from typing import List
import importlib.util

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
        def __init__(self, component: TempSensorComponent):
            super(G1_NcdAds1115_Ntc10k, self).__init__(component=component)
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
                i2c = busio.I2C(board.SCL, board.SDA)
            except:
                raise Exception("Error creating busio.I2C device!")
            try:
                self.ads = ADS.ADS1115(i2c)
            except:
                raise Exception("Error creating ADS.ADS1115(i2c) object")

        def read_telemetry_value(self) -> int:
            if self.channel_idx == 0:
                channel = AnalogIn(self.ads, ADS.P0)
            elif self.channel_idx == 1:
                channel = AnalogIn(self.ads, ADS.P1)
            elif self.channel_idx == 2:
                channel = AnalogIn(self.ads, ADS.P2)
            elif self.channel_idx == 3:
                channel = AnalogIn(self.ads, ADS.P3)
            try:
                value = channel.voltage
                # value = self.channel.value
            except:
                return DEFAULT_BAD_VALUE
            return int(value * 1000)
else:
    from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver

    class G1_NcdAds1115_Ntc10k(TempSensorDriver):

        def read_telemetry_value(self) -> int:
            raise NotImplementedError
