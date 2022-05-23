"""Makes GridWorksSerial protocol GsDispatch100 with MpAlias d"""
import struct
from typing import List, Tuple, Optional
from schema.errors import MpSchemaError
from schema.gs.gs_dispatch_1_0_0 import GsDispatch100


class GsDispatch100_Maker():
    mp_alias = 'd'
    
    @classmethod
    def binary_to_type(cls, b: bytes) -> GsDispatch100:
        (power,) = struct.unpack("<h", b)
        t = GsDispatch100(Power=power)
        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create type due to these errors: {errors}")
        return t

    @classmethod
    def type_is_valid(cls, serial_payload: bytes) -> Tuple[bool, Optional[List[str]]]:
        try:
            t = cls.binary_to_type(serial_payload)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return t.is_valid()

    def __init__(self,power):
        t = GsDispatch100(Power=power)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t
