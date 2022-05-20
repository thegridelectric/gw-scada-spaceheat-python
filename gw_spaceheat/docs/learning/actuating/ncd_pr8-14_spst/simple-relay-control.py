# This script works once you've gotten smbus set up on your pi. Read docs
from drivers.mcp23008 import mcp23008
import smbus

bus = smbus.SMBus(1)

#define which GPIOs are to be used as outputs. By default all GPIOs are defined as inputs.
#pass the number of the GPIOs in a set to the object. 0 is the first relay 1 is the second etc.
gpio_output_map =  {0,1,2,3}
#kwargs is a Python set that contains the address of your device and the output map to be passed to the object for initialization.
kwargs = {'address': 0x20, 'gpio_output_map': gpio_output_map}
#create the MCP23008 object from the MCP23008 library and pass it the GPIO output map and address defined above
#the object requires that you pass it the bus object so that it can communicate and share the bus with other chips if necessary
m = mcp23008(bus, kwargs)

m.turn_off_relay(0)
m.turn_off_relay(1)


print(m.get_all_gpio_status() % 4)
# returns 0

m.turn_on_relay(0)

print(m.get_all_gpio_status() % 4)
# returns 1 

m.turn_on_relay(1)

print(m.get_all_gpio_status() % 4)
# returns 3
m.get_single_gpio_status(0)
# returns 1
m.get_single_gpio_status(1)
# returns 1
