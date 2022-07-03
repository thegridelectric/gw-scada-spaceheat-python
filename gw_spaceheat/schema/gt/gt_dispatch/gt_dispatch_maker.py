"""Makes gt.dispatch.110 type"""
import json

from schema.gt.gt_dispatch.gt_dispatch import GtDispatch
from schema.errors import MpSchemaError


class GtDispatch_Maker:
    type_alias = "gt.dispatch.110"

    def __init__(self,
                 sh_node_alias: str,
                 send_time_unix_ms: int,
                 relay_state: int):

        gw_tuple = GtDispatch(
            ShNodeAlias=sh_node_alias,
            SendTimeUnixMs=send_time_unix_ms,
            RelayState=relay_state,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtDispatch) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtDispatch:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtDispatch:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "SendTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SendTimeUnixMs")
        if "RelayState" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RelayState")

        gw_tuple = GtDispatch(
            TypeAlias=new_d["TypeAlias"],
            ShNodeAlias=new_d["ShNodeAlias"],
            SendTimeUnixMs=new_d["SendTimeUnixMs"],
            RelayState=new_d["RelayState"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
