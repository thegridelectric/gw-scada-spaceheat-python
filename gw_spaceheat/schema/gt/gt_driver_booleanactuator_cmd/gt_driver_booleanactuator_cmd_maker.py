"""Makes gt.driver.booleanactuator.cmd.100 type"""
import json

from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd import GtDriverBooleanactuatorCmd
from schema.errors import MpSchemaError


class GtDriverBooleanactuatorCmd_Maker:
    type_alias = "gt.driver.booleanactuator.cmd.100"

    def __init__(self,
                 relay_state: int,
                 sh_node_alias: str,
                 command_time_unix_ms: int):

        gw_tuple = GtDriverBooleanactuatorCmd(
            RelayState=relay_state,
            ShNodeAlias=sh_node_alias,
            CommandTimeUnixMs=command_time_unix_ms,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtDriverBooleanactuatorCmd) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtDriverBooleanactuatorCmd:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtDriverBooleanactuatorCmd:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "RelayState" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RelayState")
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "CommandTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing CommandTimeUnixMs")

        gw_tuple = GtDriverBooleanactuatorCmd(
            TypeAlias=new_d["TypeAlias"],
            RelayState=new_d["RelayState"],
            ShNodeAlias=new_d["ShNodeAlias"],
            CommandTimeUnixMs=new_d["CommandTimeUnixMs"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
