"""Makes gt.dispatch.boolean.local.100 type"""
import json

from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import GtDispatchBooleanLocal
from schema.errors import MpSchemaError


class GtDispatchBooleanLocal_Maker:
    type_alias = "gt.dispatch.boolean.local.100"

    def __init__(self,
                 send_time_unix_ms: int,
                 from_node_alias: str,
                 about_node_alias: str,
                 relay_state: int):

        gw_tuple = GtDispatchBooleanLocal(
            SendTimeUnixMs=send_time_unix_ms,
            FromNodeAlias=from_node_alias,
            AboutNodeAlias=about_node_alias,
            RelayState=relay_state,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtDispatchBooleanLocal) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtDispatchBooleanLocal:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtDispatchBooleanLocal:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "SendTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SendTimeUnixMs")
        if "FromNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromNodeAlias")
        if "AboutNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAlias")
        if "RelayState" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RelayState")

        gw_tuple = GtDispatchBooleanLocal(
            TypeAlias=new_d["TypeAlias"],
            SendTimeUnixMs=new_d["SendTimeUnixMs"],
            FromNodeAlias=new_d["FromNodeAlias"],
            AboutNodeAlias=new_d["AboutNodeAlias"],
            RelayState=new_d["RelayState"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
