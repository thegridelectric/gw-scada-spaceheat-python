"""Makes gt.dispatch.boolean.100 type"""
import json

from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean import GtDispatchBoolean
from schema.errors import MpSchemaError


class GtDispatchBoolean_Maker:
    type_alias = "gt.dispatch.boolean.100"

    def __init__(self,
                 about_node_alias: str,
                 to_g_node_alias: str,
                 from_g_node_alias: str,
                 from_g_node_id: str,
                 relay_state: int,
                 send_time_unix_ms: int):

        gw_tuple = GtDispatchBoolean(
            AboutNodeAlias=about_node_alias,
            ToGNodeAlias=to_g_node_alias,
            FromGNodeAlias=from_g_node_alias,
            FromGNodeId=from_g_node_id,
            RelayState=relay_state,
            SendTimeUnixMs=send_time_unix_ms,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtDispatchBoolean) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtDispatchBoolean:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtDispatchBoolean:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "AboutNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAlias")
        if "ToGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ToGNodeAlias")
        if "FromGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeAlias")
        if "FromGNodeId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeId")
        if "RelayState" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RelayState")
        if "SendTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SendTimeUnixMs")

        gw_tuple = GtDispatchBoolean(
            TypeAlias=new_d["TypeAlias"],
            AboutNodeAlias=new_d["AboutNodeAlias"],
            ToGNodeAlias=new_d["ToGNodeAlias"],
            FromGNodeAlias=new_d["FromGNodeAlias"],
            FromGNodeId=new_d["FromGNodeId"],
            RelayState=new_d["RelayState"],
            SendTimeUnixMs=new_d["SendTimeUnixMs"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
