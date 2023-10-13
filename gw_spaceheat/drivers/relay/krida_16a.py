import smbus2 as smbus
from mcp23017.ncd_driver import mcp23017
from drivers.relay.mcp23017.ncd_driver import mcp23017


bus = smbus.SMBus(1)

mcp23008_driver = mcp23017(bus, kwargs)






### CODE FROM DAN

from smbus2 import SMBus

old = 0x22
new = 0x20

bankA = 0x12  # Relays 9 - 16
bankB = 0x13  # Relays 1 - 8

def i2c_write(dev, reg, dat):
    with SMBus(1) as bus:
        toWrite = [dat]
        bus.write_i2c_block_data(dev, reg, toWrite)

def i2c_read(addr, reg):
    with SMBus(1) as bus:
        rawData = bus.read_i2c_block_data(addr, reg, 1)
        return rawData

def module_setup(addr):
    i2c_write(addr, reg=0x00, dat=0x00)
    i2c_write(addr, reg=0x01, dat=0x00)


def a1_on(addr):
    oldByte = i2c_read(addr, bankA)
    newByte = oldByte[0] | 0x80
    i2c_write(addr, bankA, newByte)

def a1_off(addr):
    oldByte = i2c_read(addr, bankA)
    newByte = oldByte[0] & 0x7F
    i2c_write(addr, bankA, newByte)

