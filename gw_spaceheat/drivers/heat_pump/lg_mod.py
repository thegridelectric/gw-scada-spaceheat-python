
from pymodbus.client.sync import ModbusTcpClient

SLAVE_ID = 0x12


HEAT_COOL_ENABLE_COIL_REGISTER = 1
# This is one we should be able to read and write

# This one we can only read
FLOW_RATE_TOO_LOW_DISCRETE_REGISTER = 1


# This one we can only read
WATER_INLET_TEMP_INPUT_REGISTER = 3




# These ones we can read and wright
OPERATING_MODE_HOLDING_REGISTER = 1
# 0 = cooling, 3 = auto, 4 = heating
CONTROL_METHOD_HOLDING_REGISTER = 2
# 0 = water outlet temp control
# 1 = water inlet temp control
# 2 = room air control
TARGET_TEMP_HOLDING_REGISTER = 3
DHW_TARGET_TEMP_HOLDING_REGISTER = 9


client = ModbusTcpClient(host="192.168.1.49")
client.connect()

client.mask_write_register

client.read_coils(address=HEAT_COOL_ENABLE_COIL_REGISTER - 1, count=1 ,unit=SLAVE_ID).bits[0]


result = client.read_discrete_inputs(address=FLOW_RATE_TOO_LOW_DISCRETE_REGISTER - 1, unit=SLAVE_ID) # not sure this actually worked

client.read_input_registers(address=WATER_INLET_TEMP_INPUT_REGISTER - 1, count=1, unit=SLAVE_ID).registers[0]


client.read_holding_registers(address=TARGET_TEMP_HOLDING_REGISTER - 1, count=1, unit=SLAVE_ID).registers[0]


client.read_holding_registers(address=CONTROL_METHOD_HOLDING_REGISTER - 1, count=1, unit=SLAVE_ID).registers[0]

client.read_holding_registers(address=DHW_TARGET_TEMP_HOLDING_REGISTER - 1, count=1, unit=SLAVE_ID).registers[0]

r = client.write_register(address=TARGET_TEMP_HOLDING_REGISTER, value=440, unit=SLAVE_ID)

