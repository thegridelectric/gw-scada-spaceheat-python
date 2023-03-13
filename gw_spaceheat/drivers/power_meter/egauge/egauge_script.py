# pick an f32
l1_v_rms = 500
l2_v_rms = 502
l1_hz = 1500
l2_hz = 1502
mains_w = 9002
mains_current_1 = 2000
mains_current_2 = 2002
spacepak_current_1 = 2012  # S7
boost_current_1 = 2014  # S8


spacepak_power_address = 9012
boost_power = 9016
glycol_pump_power = 9020  # S9
hx_pump_power = 9024  # S10
dist_pump_power = 9028

spacepak_energy = 5032
boost_energy = 5040

import socket
import struct
import time

from pyModbusTCP.client import ModbusClient
from rich import print
from rich.traceback import install

install(show_locals=True)


def readT16FromEGauge(addr):
    regs_l = c.read_input_registers(addr, 8)
    packed = struct.pack(
        ">HHHHHHHH",
        regs_l[0],
        regs_l[1],
        regs_l[2],
        regs_l[3],
        regs_l[4],
        regs_l[5],
        regs_l[6],
        regs_l[7],
    )
    unpacked = struct.unpack(">16s", packed)[0]
    return unpacked


def readS64FromEgauge(addr):
    regs_l = c.read_input_registers(addr, 4)
    packed = struct.pack(">HHHH", regs_l[0], regs_l[1], regs_l[2], regs_l[3])
    unpacked = struct.unpack(">q", packed)[0]
    return unpacked


def readF32FromEgauge(addr):  # Read a 32bit Float
    regs_l = c.read_input_registers(addr, 2)
    packed = struct.pack(">HH", regs_l[0], regs_l[1])
    unpacked = struct.unpack(">f", packed)[0]
    return unpacked


def readU32FromEgauge(addr):  # Read a 32bit Unsigned Int
    regs_l = c.read_input_registers(addr, 2)
    if regs_l:
        packed = struct.pack(">HH", regs_l[0], regs_l[1])
        unpacked = struct.unpack(">I", packed)[0]
        return unpacked
    else:
        print("unable to read registers")
        return 0


# Register Addr
regAddrLocalTime = 0  # u32 Unit:s
# regAddrLoad1        = 9000    #f32 Unit: W

# init modbus client
hostname = "eGauge14875.local"
host = socket.gethostbyname(hostname)
print(f"host: {hostname} -> {host}")
c = ModbusClient(
    host=host, port=502, unit_id=1, timeout=5.0, auto_open=True, debug=False
)
print(f"ModbusClient: {c}")
print(f"open: {c.open()}")


# timestamp=readU32FromEgauge(regAddrLocalTime)
l1_v_rms_val = readF32FromEgauge(l1_v_rms)
l2_v_rms_val = readF32FromEgauge(l2_v_rms)

mains_current_1_micro_amps = int(readF32FromEgauge(mains_current_1) * 1_000_000)
mains_current_2_val = readF32FromEgauge(mains_current_2)
boost_current_1_val = readF32FromEgauge(boost_current_1)
spacepak_current_1_val = readF32FromEgauge(spacepak_current_1)


spacepak_energy_val = readS64FromEgauge(spacepak_energy)
spacepak_energy_milli_watt_hours = int(spacepak_energy_val / 3.6)
boost_energy_val = readS64FromEgauge(boost_energy)
boost_energy_milli_watt_hours = int(boost_energy_val / 3.6)
print(f"Voltage: L1: {round(l1_v_rms_val,3)} VRMS,  L2: {round(l2_v_rms_val,3)} VRMS")
print(
    f"Current: Hp: {round(spacepak_current_1_val,1)} A Boost:{round(boost_current_1_val,1)} A, mains1: {round(mains_current_1_micro_amps,1)} MicroAmps, mains2: {round(mains_current_2_val,2)} A"
)

glycol_pump_power_val = readF32FromEgauge(glycol_pump_power)
hx_pump_power_val = readF32FromEgauge(hx_pump_power)
dist_pump_power_val = readF32FromEgauge(dist_pump_power)
print(
    f"Signal power. Glycol: {int(glycol_pump_power_val)} W, Hx: {int(hx_pump_power_val)} W, Dist: {int(dist_pump_power_val)} W"
)

boost_power_val = readF32FromEgauge(boost_power)
spacepak_power = readF32FromEgauge(spacepak_power_address)
mains_w_val = readF32FromEgauge(mains_w)
print(
    f"Power: Spacepak: {int(spacepak_power)} W, boost: {int(boost_power_val)} W, Mains: {int(mains_w_val)} W"
)

print(f"Spacepak cumulative energy: {spacepak_energy_milli_watt_hours} milli Wh")
print(
    f"Spacepak cumulative energy: {round(spacepak_energy_milli_watt_hours / 1000000, 2)} kWh"
)

print(f"Boost cumulative energy: {boost_energy_milli_watt_hours} milli Wh")

l1_hz_val = readF32FromEgauge(l1_hz)
l2_hz_val = readF32FromEgauge(l2_hz)

print(f"L1 Freq: {l1_hz_val} Hz, L2 Freq: {l2_hz_val}")

hardware_id_address = 100

hardware_id = readT16FromEGauge(hardware_id_address)
print(f"Hardware Id: {hardware_id}")
