"""Makes gt.sh.status.110 type"""
import json
from typing import List

from schema.gt.gt_sh_status.gt_sh_status import GtShStatus
from schema.errors import MpSchemaError
from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status_maker import (
    GtShSimpleTelemetryStatus,
    GtShSimpleTelemetryStatus_Maker,
)
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status_maker import (
    GtShBooleanactuatorCmdStatus,
    GtShBooleanactuatorCmdStatus_Maker,
)
from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status_maker import (
    GtShMultipurposeTelemetryStatus,
    GtShMultipurposeTelemetryStatus_Maker,
)


class GtShStatus_Maker:
    type_alias = "gt.sh.status.110"

    def __init__(self,
                 slot_start_unix_s: int,
                 simple_telemetry_list: List[GtShSimpleTelemetryStatus],
                 about_g_node_alias: str,
                 booleanactuator_cmd_list: List[GtShBooleanactuatorCmdStatus],
                 from_g_node_alias: str,
                 multipurpose_telemetry_list: List[GtShMultipurposeTelemetryStatus],
                 from_g_node_id: str,
                 status_uid: str,
                 reporting_period_s: int):

        gw_tuple = GtShStatus(
            SlotStartUnixS=slot_start_unix_s,
            SimpleTelemetryList=simple_telemetry_list,
            AboutGNodeAlias=about_g_node_alias,
            BooleanactuatorCmdList=booleanactuator_cmd_list,
            FromGNodeAlias=from_g_node_alias,
            MultipurposeTelemetryList=multipurpose_telemetry_list,
            FromGNodeId=from_g_node_id,
            StatusUid=status_uid,
            ReportingPeriodS=reporting_period_s,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShStatus:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "SlotStartUnixS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SlotStartUnixS")
        if "SimpleTelemetryList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SimpleTelemetryList")
        simple_telemetry_list = []
        for elt in new_d["SimpleTelemetryList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of SimpleTelemetryList must be "
                    "GtShSimpleTelemetryStatus but not even a dict!"
                )
            simple_telemetry_list.append(
                GtShSimpleTelemetryStatus_Maker.dict_to_tuple(elt)
            )
        new_d["SimpleTelemetryList"] = simple_telemetry_list
        if "AboutGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutGNodeAlias")
        if "BooleanactuatorCmdList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing BooleanactuatorCmdList")
        booleanactuator_cmd_list = []
        for elt in new_d["BooleanactuatorCmdList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of BooleanactuatorCmdList must be "
                    "GtShBooleanactuatorCmdStatus but not even a dict!"
                )
            booleanactuator_cmd_list.append(
                GtShBooleanactuatorCmdStatus_Maker.dict_to_tuple(elt)
            )
        new_d["BooleanactuatorCmdList"] = booleanactuator_cmd_list
        if "FromGNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeAlias")
        if "MultipurposeTelemetryList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing MultipurposeTelemetryList")
        multipurpose_telemetry_list = []
        for elt in new_d["MultipurposeTelemetryList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of MultipurposeTelemetryList must be "
                    "GtShMultipurposeTelemetryStatus but not even a dict!"
                )
            multipurpose_telemetry_list.append(
                GtShMultipurposeTelemetryStatus_Maker.dict_to_tuple(elt)
            )
        new_d["MultipurposeTelemetryList"] = multipurpose_telemetry_list
        if "FromGNodeId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing FromGNodeId")
        if "StatusUid" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing StatusUid")
        if "ReportingPeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportingPeriodS")

        gw_tuple = GtShStatus(
            TypeAlias=new_d["TypeAlias"],
            SlotStartUnixS=new_d["SlotStartUnixS"],
            SimpleTelemetryList=new_d["SimpleTelemetryList"],
            AboutGNodeAlias=new_d["AboutGNodeAlias"],
            BooleanactuatorCmdList=new_d["BooleanactuatorCmdList"],
            FromGNodeAlias=new_d["FromGNodeAlias"],
            MultipurposeTelemetryList=new_d["MultipurposeTelemetryList"],
            FromGNodeId=new_d["FromGNodeId"],
            StatusUid=new_d["StatusUid"],
            ReportingPeriodS=new_d["ReportingPeriodS"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
