"""Makes snapshot.spaceheat.100 type"""
import json

from schema.gt.snapshot_spaceheat.snapshot_spaceheat import SnapshotSpaceheat
from schema.errors import MpSchemaError
from schema.gt.telemetry_snapshot_spaceheat.telemetry_snapshot_spaceheat_maker import (
    TelemetrySnapshotSpaceheat,
    TelemetrySnapshotSpaceheat_Maker,
)


class SnapshotSpaceheat_Maker:
    type_alias = "snapshot.spaceheat.100"

    def __init__(self,
                 from_g_node_alias: str,
                 from_g_node_instance_id: str,
                 snapshot: TelemetrySnapshotSpaceheat):

        gw_tuple = SnapshotSpaceheat(
            FromGNodeAlias=from_g_node_alias,
            FromGNodeInstanceId=from_g_node_instance_id,
            Snapshot=snapshot,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: SnapshotSpaceheat) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> SnapshotSpaceheat:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> SnapshotSpaceheat:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "FromGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeAlias")
        if "FromGNodeInstanceId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeInstanceId")
        if "Snapshot" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Snapshot")
        if not isinstance(new_d["Snapshot"], dict):
            raise MpSchemaError(f"d['Snapshot'] {new_d['Snapshot']} must be a TelemetrySnapshotSpaceheat!")
        snapshot = TelemetrySnapshotSpaceheat_Maker.dict_to_tuple(new_d["Snapshot"])
        new_d["Snapshot"] = snapshot

        gw_tuple = SnapshotSpaceheat(
            TypeAlias=new_d["TypeAlias"],
            FromGNodeAlias=new_d["FromGNodeAlias"],
            FromGNodeInstanceId=new_d["FromGNodeInstanceId"],
            Snapshot=new_d["Snapshot"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
