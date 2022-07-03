"""Makes gt.sh.cli.atn.cmd.100 type"""
import json

from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd import GtShCliAtnCmd
from schema.errors import MpSchemaError


class GtShCliAtnCmd_Maker:
    type_alias = "gt.sh.cli.atn.cmd.100"

    def __init__(self,
                 send_snapshot: bool):

        gw_tuple = GtShCliAtnCmd(
            SendSnapshot=send_snapshot,
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
        if "SendSnapshot" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SendSnapshot")

        gw_tuple = GtShCliAtnCmd(
            TypeAlias=new_d["TypeAlias"],
            SendSnapshot=new_d["SendSnapshot"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
