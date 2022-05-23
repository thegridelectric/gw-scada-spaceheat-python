"""Makes GridWorksSerial protocol gs.pwr.100 with MpAlias p"""
import struct
from typing import List, Tuple, Optional
from schema.errors import MpSchemaError
from schema.gs.gs_pwr_1_0_0 import GsPwr100


class GsPwr100_Maker():
    mp_alias = 'p'
    
    @classmethod
    def binary_to_type(cls, b: bytes) -> GsPwr100:
        (power,) = struct.unpack("<h", b)
        p = GsPwr100(Power=power)
        is_valid, errors = p.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create type due to these errors: {errors}")
        return p

    @classmethod
    def type_is_valid(cls, serial_payload: bytes) -> Tuple[bool, Optional[List[str]]]:
        try:
            t = cls.binary_to_type(serial_payload)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return t.is_valid()

    def __init__(self,power):
        t = GsPwr100(Power=power)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create type due to these errors: {errors}")
        self.type = t

