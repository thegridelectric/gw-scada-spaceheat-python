import time
# from totalizer_code.AtlasI2C import AtlasI2C
from AtlasI2C import (
    AtlasI2C
)
device = AtlasI2C()
device_address = 104


device.set_i2c_address(device_address)
response = device.query("I")
try:
    moduletype = response.split(",")[1]
    name = device.query("name,?").split(",")[1]
except IndexError:
    print(">> WARNING: device at I2C address " + str(device_address)
          + " has not been identified as an EZO device, and will not be queried")

dev = AtlasI2C(address=device_address, moduletype=moduletype, name=name)


dev.write("Clear")

dev.write("R")
time.sleep(0.3)
v0 = dev.read()

try:
    val = float(v0.split(':')[1].split('\x00')[0])
except:
    print("Failed to get a reading")
print(val)

dev.write("CF, .264")
time.sleep(0.3)
dev.write("CF,?")
time.sleep(0.3)
v0 = dev.read()
try:
    r = v0.split(':')[1].split('\x00')[0].split(',')
except:
    print("error checking conversion factor")
assert r[1] == 'CF'
assert r[2] == '0.264'


dev.write("O,TV,1")
time.sleep(0.3)
dev.write("O,FR,0")
time.sleep(0.3)
dev.write("O,?")
time.sleep(0)
v0 = dev.read()
try:
    r = v0.split(':')[1].split('\x00')[0].split(',')
except:
    print("error checking output")
assert len(r) == 2
assert r[1] == 'TV'

while True:

    dev.write("R")
    time.sleep(0.3)
    v0 = dev.read()
    float(v0.split(':')[1].split('\x00')[0])
    print(v0)
