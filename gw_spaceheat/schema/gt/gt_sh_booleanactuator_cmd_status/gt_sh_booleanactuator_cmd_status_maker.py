"""Makes gt.sh.booleanactuator.cmd.status.100 type"""
import json
from typing import List

from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from schema.errors import MpSchemaError


class GtShBooleanactuatorCmdStatus_Maker:
    type_alias = "gt.sh.booleanactuator.cmd.status.100"

    def __init__(self,
                 sh_node_alias: str,
                 relay_state_command_list: List[int],
                 command_time_unix_ms_list: List[int]):

        gw_tuple = GtShBooleanactuatorCmdStatus(
            ShNodeAlias=sh_node_alias,
            RelayStateCommandList=relay_state_command_list,
            CommandTimeUnixMsList=command_time_unix_ms_list,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShBooleanactuatorCmdStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShBooleanactuatorCmdStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShBooleanactuatorCmdStatus:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "RelayStateCommandList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RelayStateCommandList")
        if "CommandTimeUnixMsList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing CommandTimeUnixMsList")

        gw_tuple = GtShBooleanactuatorCmdStatus(
            TypeAlias=new_d["TypeAlias"],
            ShNodeAlias=new_d["ShNodeAlias"],
            RelayStateCommandList=new_d["RelayStateCommandList"],
            CommandTimeUnixMsList=new_d["CommandTimeUnixMsList"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
