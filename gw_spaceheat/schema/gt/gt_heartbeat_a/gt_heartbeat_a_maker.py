"""Makes gt.heartbeat.a.100 type"""
import json

from schema.gt.gt_heartbeat_a.gt_heartbeat_a import GtHeartbeatA
from schema.errors import MpSchemaError


class GtHeartbeatA_Maker:
    type_alias = "gt.heartbeat.a.100"

    def __init__(self):

        gw_tuple = GtHeartbeatA(
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtHeartbeatA) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtHeartbeatA:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtHeartbeatA:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")

        gw_tuple = GtHeartbeatA(
            TypeAlias=new_d["TypeAlias"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
