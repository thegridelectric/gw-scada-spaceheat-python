from pymodbus.client.sync import ModbusSerialClient
import serial.rs485
import numpy as np
import time

# Register address
SERIAL_NUMBER_ADDR = 130
CURRENT_RMS_MICRO_A_ADDR = 3000
VoltageRmsV_addr = 3028
ActivePowerRmsW_addr = 3054
ReactivePowerRmsVar_addr = 3068
ApparentPowerRmsVa_addr = 3076
PowerFactor_addr = 3084
Frequency_addr = 3110


def init_logging(enable_serial):
    if(enable_serial):
        import logging
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)


def init_modbus():
    Port = '/dev/ttyUSB0'
    Baud = 9600
    ser = serial.rs485.RS485(port=Port, baudrate=Baud)
    ser.rs485_mode = serial.rs485.RS485Settings(
        rts_level_for_tx=False, rts_level_for_rx=True, delay_before_tx=0.0, delay_before_rx=-0.0)
    return ser


def connect_modbus(interface):
    client = ModbusSerialClient(method='rtu')
    client.socket = interface
    client.connect()
    return client


def close_conn(interface):
    interface.close()


def read_register_raw(client, reg_addr, bytes_to_read=2, dtype=np.uint16):
    result = client.read_holding_registers(address=reg_addr - 1,
                                           count=bytes_to_read,
                                           unit=12)
    data_bytes = np.array([result.registers[1],
                           result.registers[0]], dtype=dtype)
    return data_bytes


def read_register(client, reg_addr, bytes_to_read=2):
    # Voltage reading, Page 60, reg 3028
    data_bytes = read_register_raw(client, reg_addr, bytes_to_read)
    data_as_float = data_bytes.view(dtype=np.float32)
    # print(data_as_float)
    return data_as_float[0]


def read_hw_uid(client):
    data_bytes = read_register_raw(client, SERIAL_NUMBER_ADDR, 2, np.uint32)
    return f"{str(data_bytes[0])}_{str(data_bytes[1])}"


if __name__ == "__main__":
    try:
        # Initialize the client
        init_logging(False)
        interface = init_modbus()
        client = connect_modbus(interface)

        while(True):
            # Read the registers
            CurrentRmsA = read_register(client, CURRENT_RMS_MICRO_A_ADDR)
            VoltageRmsV = read_register(client, VoltageRmsV_addr)
            ActivePowerRmsW = read_register(client, ActivePowerRmsW_addr)
            ReactivePowerRmsVar = read_register(client, ReactivePowerRmsVar_addr)
            ApparentPowerRmsVa = read_register(client, ApparentPowerRmsVa_addr)
            PowerFactor = read_register(client, PowerFactor_addr)
            Frequency = read_register(client, Frequency_addr)

            # Print the data
            print("-----------------------------------------")
            print("CurrentRmsA \t\t: %f A" % (CurrentRmsA))
            print("VoltageRmsV \t\t: %f V" % (VoltageRmsV))
            print("ActivePowerRmsW \t: %f kW" % (ActivePowerRmsW))
            print("ReactivePowerRmsVar \t: %f kVAR" % (ReactivePowerRmsVar))
            print("ApparentPowerRmsVa \t: %f kVA" % (ApparentPowerRmsVa))
            print("PowerFactor \t\t: %f" % (PowerFactor))
            print("Frequency \t\t: %f Hz" % (Frequency))

            time.sleep(1)

    finally:
        print("Closing client")
        close_conn(client)
