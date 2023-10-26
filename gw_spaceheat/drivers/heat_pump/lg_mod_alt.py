from pyModbusTCP.client import ModbusClient
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