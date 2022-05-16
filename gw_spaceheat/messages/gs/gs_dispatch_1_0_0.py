"""MessageMaker for GridWorksSerial protocol GsPwr100 with MpAlias p"""
import struct
from typing import List, Tuple, Optional
from messages.errors import MpSchemaError
from messages.gs.gs_pwr_1_0_0_payload import GsPwr100Payload


class Gs_Pwr_1_0_0():
    mp_alias = 'p'
    
    @classmethod
    def binary_to_type(cls, b: bytes) -> GsPwr100Payload:
        (power,) = struct.unpack("<h", b)
        p = GsPwr100Payload(Power=power)
        is_valid, errors = p.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        return p

    @classmethod
    def payload_is_valid(cls, serial_payload: bytes) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.binary_to_payload(serial_payload)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,power):
        p = GsPwr100Payload(Power=power)

        is_valid, errors = p.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.payload = p

