"""Makes gt.sh.cli.scada.response.100 type"""

import json

from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response import GtShCliScadaResponse
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import (
    GtShStatusSnapshot,
    GtShStatusSnapshot_Maker,
)
from schema.errors import MpSchemaError


class GtShCliScadaResponse_Maker:
    type_alias = "gt.sh.cli.scada.response.100"

    def __init__(self, snapshot: GtShStatusSnapshot):

        tuple = GtShCliScadaResponse(Snapshot=snapshot)
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShCliScadaResponse) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShCliScadaResponse:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShCliScadaResponse:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "Snapshot" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Snapshot")
        if not isinstance(new_d["Snapshot"], dict):
            raise MpSchemaError(f"d['Snapshot'] {new_d['Snapshot']} must be a GtShStatusSnapshot!")
        snapshot = GtShStatusSnapshot_Maker.dict_to_tuple(new_d["Snapshot"])
        new_d["Snapshot"] = snapshot
        tuple = GtShCliScadaResponse(TypeAlias=new_d["TypeAlias"], Snapshot=new_d["Snapshot"])
        tuple.check_for_errors()
        return tuple
