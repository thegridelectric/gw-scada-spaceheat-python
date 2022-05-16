import time
import pendulum
import struct


def is_reasonable_unix_time_ms(candidate):
    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp*1000 > candidate:
        return False
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp*1000 < candidate:
        return False
    return True

def is_unsigned_short(candidate):
    try:
        struct.pack("H",candidate)
    except:
        print(f"requires 0 <= number <= 65535")
        return False
    return True

def is_short_integer(candidate):
    try:
        struct.pack("h",candidate)
    except:
        print("short format requires (-32767 -1) <= number <= 32767")
        return False
    return True