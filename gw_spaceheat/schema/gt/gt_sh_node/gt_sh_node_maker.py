"""Makes gt.sh.node.120 type"""

import json
from typing import Optional

from data_classes.sh_node import ShNode
from schema.enums.actor_class.actor_class_map import ActorClass, ActorClassMap
from schema.enums.role.role_map import Role, RoleMap
from schema.errors import MpSchemaError
from schema.gt.gt_sh_node.gt_sh_node import GtShNode


class GtShNode_Maker:
    type_alias = "gt.sh.node.120"

    def __init__(
        self,
        sh_node_id: str,
        alias: str,
        actor_class: ActorClass,
        role: Role,
        component_id: str,
        display_name: Optional[str],
        reporting_sample_period_s: Optional[int],
    ):

        gw_tuple = GtShNode(
            ShNodeId=sh_node_id,
            DisplayName=display_name,
            ActorClass=actor_class,
            Role=role,
            ReportingSamplePeriodS=reporting_sample_period_s,
            Alias=alias,
            ComponentId=component_id,
        )
        gw_tuple.check_for_errors()
        self.tuple: GtShNode = gw_tuple

    @classmethod
    def tuple_to_type(cls, gw_tuple: GtShNode) -> str:
        gw_tuple.check_for_errors()
        return gw_tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShNode:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShNode:
        if "ShNodeId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ShNodeId")
        if "Alias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Alias")
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ActorClassGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ActorClassGtEnumSymbol")
        d["ActorClass"] = ActorClassMap.gt_to_local(d["ActorClassGtEnumSymbol"])
        if "RoleGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing RoleGtEnumSymbol")
        d["Role"] = RoleMap.gt_to_local(d["RoleGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "ReportingSamplePeriodS" not in d.keys():
            d["ReportingSamplePeriodS"] = None

        gw_tuple = GtShNode(
            ShNodeId=d["ShNodeId"],
            DisplayName=d["DisplayName"],
            ActorClass=d["ActorClass"],
            Role=d["Role"],
            ReportingSamplePeriodS=d["ReportingSamplePeriodS"],
            Alias=d["Alias"],
            ComponentId=d["ComponentId"],
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: GtShNode) -> ShNode:
        s = {
            "sh_node_id": t.ShNodeId,
            "display_name": t.DisplayName,
            "reporting_sample_period_s": t.ReportingSamplePeriodS,
            "alias": t.Alias,
            "component_id": t.ComponentId,
            "actor_class_gt_enum_symbol": ActorClassMap.local_to_gt(t.ActorClass),
            "role_gt_enum_symbol": RoleMap.local_to_gt(t.Role),
        }
        if s["sh_node_id"] in ShNode.by_id.keys():
            dc = ShNode.by_id[s["sh_node_id"]]
        else:
            dc = ShNode(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ShNode) -> Optional[GtShNode]:
        if dc is None:
            return None
        t = GtShNode(
            ShNodeId=dc.sh_node_id,
            DisplayName=dc.display_name,
            ActorClass=dc.actor_class,
            Role=dc.role,
            ReportingSamplePeriodS=dc.reporting_sample_period_s,
            Alias=dc.alias,
            ComponentId=dc.component_id,
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
