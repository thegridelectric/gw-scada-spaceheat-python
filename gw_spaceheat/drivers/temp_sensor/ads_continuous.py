import time
import math
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC objects using the I2C bus
ads = {}
ads[0] = ADS.ADS1115(address=int("0x48", 16), i2c=i2c)
ads[1]= ADS.ADS1115(address=int("0x49", 16), i2c=i2c)
ads[2] = ADS.ADS1115(address=int("0x4b", 16), i2c=i2c)


while True:
    v1 = round(AnalogIn(ads[0], ADS.P0).voltage,3)
    v2 = round(AnalogIn(ads[0], ADS.P1).voltage,3)
    v3 = round(AnalogIn(ads[0], ADS.P2).voltage,3)
    v4 = round(AnalogIn(ads[0], ADS.P3).voltage,3)
    v5 = round(AnalogIn(ads[1], ADS.P0).voltage,3)
    v6 = round(AnalogIn(ads[1], ADS.P1).voltage,3)
    v7 = round(AnalogIn(ads[1], ADS.P2).voltage,3)
    v8 = round(AnalogIn(ads[1], ADS.P3).voltage,3)
    v9 = round(AnalogIn(ads[2], ADS.P0).voltage,3)
    v10 = round(AnalogIn(ads[2], ADS.P1).voltage,3)
    v11 = round(AnalogIn(ads[2], ADS.P2).voltage,3)
    v12 = round(AnalogIn(ads[2], ADS.P3).voltage,3)
    print(f"1: {v1}V 2: {v2}V 3: {v3}V 4: {v4}V 5: {v5}V 6: {v6}V 7: {v7}V 8: {v8}V 9:{v9}V 10: {v10}V 11: {v11}V 12: {v12}V")
    time.sleep(0.5)