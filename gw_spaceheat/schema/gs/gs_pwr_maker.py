"""Makes GridWorksSerial protocol gs.pwr.100 with MpAlias p"""
import struct
from schema.gs.gs_pwr import GsPwr


class GsPwr_Maker():
    type_alias = 'p'
    
    def __init__(self,power):
        tuple = GsPwr(Power=power)
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GsPwr) -> bytes:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> GsPwr:
        (power,) = struct.unpack("<h", b)
        tuple = GsPwr(Power=power)
        tuple.check_for_errors
        return tuple
