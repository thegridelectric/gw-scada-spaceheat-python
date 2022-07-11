"""Makes spaceheat.node.gt.100 type"""
import json
from typing import Optional
from data_classes.sh_node import ShNode

from schema.gt.spaceheat_node_gt.spaceheat_node_gt import SpaceheatNodeGt
from schema.errors import MpSchemaError
from schema.enums.role.role_map import (
    Role,
    RoleMap,
)
from schema.enums.actor_class.actor_class_map import (
    ActorClass,
    ActorClassMap,
)


class SpaceheatNodeGt_Maker:
    type_alias = "spaceheat.node.gt.100"

    def __init__(self,
                 alias: str,
                 role: Role,
                 actor_class: ActorClass,
                 sh_node_id: str,
                 reporting_sample_period_s: Optional[int],
                 component_id: Optional[str],
                 rated_voltage_v: Optional[int],
                 display_name: Optional[str],
                 typical_voltage_v: Optional[int]):

        gw_tuple = SpaceheatNodeGt(
            Alias=alias,
            ReportingSamplePeriodS=reporting_sample_period_s,
            Role=role,
            ComponentId=component_id,
            RatedVoltageV=rated_voltage_v,
            ActorClass=actor_class,
            ShNodeId=sh_node_id,
            DisplayName=display_name,
            TypicalVoltageV=typical_voltage_v,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: SpaceheatNodeGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> SpaceheatNodeGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> SpaceheatNodeGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "Alias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Alias")
        if "ReportingSamplePeriodS" not in new_d.keys():
            new_d["ReportingSamplePeriodS"] = None
        if "RoleGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RoleGtEnumSymbol")
        new_d["Role"] = RoleMap.gt_to_local(new_d["RoleGtEnumSymbol"])
        if "ComponentId" not in new_d.keys():
            new_d["ComponentId"] = None
        if "RatedVoltageV" not in new_d.keys():
            new_d["RatedVoltageV"] = None
        if "ActorClassGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ActorClassGtEnumSymbol")
        new_d["ActorClass"] = ActorClassMap.gt_to_local(new_d["ActorClassGtEnumSymbol"])
        if "ShNodeId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeId")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "TypicalVoltageV" not in new_d.keys():
            new_d["TypicalVoltageV"] = None

        gw_tuple = SpaceheatNodeGt(
            TypeAlias=new_d["TypeAlias"],
            Alias=new_d["Alias"],
            ReportingSamplePeriodS=new_d["ReportingSamplePeriodS"],
            Role=new_d["Role"],
            ComponentId=new_d["ComponentId"],
            RatedVoltageV=new_d["RatedVoltageV"],
            ActorClass=new_d["ActorClass"],
            ShNodeId=new_d["ShNodeId"],
            DisplayName=new_d["DisplayName"],
            TypicalVoltageV=new_d["TypicalVoltageV"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: SpaceheatNodeGt) -> ShNode:
        s = {
            "alias": t.Alias,
            "reporting_sample_period_s": t.ReportingSamplePeriodS,
            "rated_voltage_v": t.RatedVoltageV,
            "sh_node_id": t.ShNodeId,
            "display_name": t.DisplayName,
            "typical_voltage_v": t.TypicalVoltageV,
            "component_id": t.ComponentId,
            "role_gt_enum_symbol": RoleMap.local_to_gt(t.Role),
            "actor_class_gt_enum_symbol": ActorClassMap.local_to_gt(t.ActorClass),
            #
        }
        if s["sh_node_id"] in ShNode.by_id.keys():
            dc = ShNode.by_id[s["sh_node_id"]]
        else:
            dc = ShNode(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ShNode) -> SpaceheatNodeGt:
        if dc is None:
            return None
        t = SpaceheatNodeGt(
            Alias=dc.alias,
            ReportingSamplePeriodS=dc.reporting_sample_period_s,
            Role=dc.role,
            RatedVoltageV=dc.rated_voltage_v,
            ActorClass=dc.actor_class,
            ShNodeId=dc.sh_node_id,
            DisplayName=dc.display_name,
            TypicalVoltageV=dc.typical_voltage_v,
            ComponentId=dc.component_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ShNode:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ShNode) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ShNode:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
