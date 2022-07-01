"""Makes GridWorksSerial protocol GsDispatch with MpAlias d"""
import struct
from schema.gs.gs_dispatch import GsDispatch


class GsDispatch_Maker:
    type_alias = "d"

    def __init__(self, relay_state):
        tuple = GsDispatch(RelayState=relay_state)
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GsDispatch) -> bytes:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> GsDispatch:
        (relay_state,) = struct.unpack("<h", b)
        tuple = GsDispatch(RelayState=relay_state)
        tuple.check_for_errors
        return tuple
