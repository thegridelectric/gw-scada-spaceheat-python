import pendulum
import struct
import string

def check_is_64_bit_hex(candidate):
    if len(candidate) != 8:
        raise Exception(f"Wrong number of bits for 64 bit hex! {candidate}")
    if not all(c in string.hexdigits for c in candidate):
        raise Exception(f"All digits must be hex! {candidate}")
    return True

def is_recognized_component_manufacturer(candidate):
    #TODO: add
    return True

def is_recognized_component_type(candidate):
    #TODO: add
    return True

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

def is_uuid_canonical_textual(candidate):
    try:
        x = candidate.split('-')
    except AttributeError:
        return False
    if len(x) != 5:
        return False
    for hex_word in x:
        try:
            y = int(hex_word, 16)
        except ValueError:
            return False
    if len(x[0]) != 8:
        return False
    if len(x[1]) != 4:
        return False
    if len(x[2]) != 4:
        return False
    if len(x[3]) != 4:
        return False
    if len(x[4]) != 12:
        return False
    return True


