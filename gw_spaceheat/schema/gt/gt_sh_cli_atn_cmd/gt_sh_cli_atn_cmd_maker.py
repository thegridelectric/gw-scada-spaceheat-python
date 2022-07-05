"""Makes gt.sh.cli.atn.cmd.110 type"""
import json

from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd import GtShCliAtnCmd
from schema.errors import MpSchemaError


class GtShCliAtnCmd_Maker:
    type_alias = "gt.sh.cli.atn.cmd.110"

    def __init__(self,
                 from_g_node_alias: str,
                 send_snapshot: bool,
                 from_g_node_id: str):

        gw_tuple = GtShCliAtnCmd(
            FromGNodeAlias=from_g_node_alias,
            SendSnapshot=send_snapshot,
            FromGNodeId=from_g_node_id,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShCliAtnCmd) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShCliAtnCmd:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShCliAtnCmd:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "FromGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeAlias")
        if "SendSnapshot" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SendSnapshot")
        if "FromGNodeId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeId")

        gw_tuple = GtShCliAtnCmd(
            TypeAlias=new_d["TypeAlias"],
            FromGNodeAlias=new_d["FromGNodeAlias"],
            SendSnapshot=new_d["SendSnapshot"],
            FromGNodeId=new_d["FromGNodeId"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
