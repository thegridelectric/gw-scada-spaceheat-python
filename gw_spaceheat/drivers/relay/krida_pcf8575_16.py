import board
import adafruit_pcf8575
import time

i2c = board.I2C()
pcf = adafruit_pcf8575.PCF8575(i2c)

r1 = pcf.get_pin(0)
r1.switch_to_output(value=True)
r1.value = False
r1.value = True

r2 = pcf.get_pin(1)
r2.switch_to_output(value=True)

r2.value = False
r2.value = True

def initialize_relays():
    for i in range(16):
        r = pcf.get_pin(i)
        r.switch_to_output(value=True)
        print(f"value of relay {i+1} is {r.value}")
        time.sleep(1)
    

r = pcf.get_pin(0)
r.switch_to_output(value=True)
r.value = False
r.value = True