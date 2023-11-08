import logging
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.transaction import _logger
import serial.rs485
import numpy as np

_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


PORT = "/dev/ttyACM0"
BAUD = 9600
SLAVE_ID=8

ERROR_REGISTER = 100
OPERATION_REGISTER = 1

def init_modbus():
    Port = PORT
    Baud = BAUD
    ser = serial.rs485.RS485(port=Port, baudrate=Baud)
    ser.rs485_mode = serial.rs485.RS485Settings(
        rts_level_for_tx=False, rts_level_for_rx=True, delay_before_tx=0.0, delay_before_rx=-0.0
    )
    return ser

def connect_modbus(interface):
    client = ModbusSerialClient(method="rtu")
    client.socket = interface
    client.connect()
    return client

interface = init_modbus()

client = connect_modbus(interface)
result = client.read_holding_registers(address=0,count=1,unit=8)

result = client.read_input_registers(address=ERROR_REGISTER - 1, count=2, unit=8)

data_bytes = np.array([result.registers[1], result.registers[0]], dtype=np.uint16)

result = client.read_coils(address=OPERATION_REGISTER-1,count=1,unit=8)




interface = init_modbus()