"""Makes gt.sh.node.110 type"""

import json
from typing import Dict, Optional
from data_classes.sh_node import ShNode

from schema.gt.gt_sh_node.gt_sh_node import GtShNode
from schema.errors import MpSchemaError
from schema.enums.role.role_map import Role, RoleMap


class GtShNode_Maker():
    type_alias = 'gt.sh.node.110'

    def __init__(self,
                 sh_node_id: str,
                 alias: str,
                 role: Role,
                 has_actor: bool,
                 component_id: Optional[str],
                 display_name: Optional[str]):

        tuple = GtShNode(ShNodeId=sh_node_id,
                                          Alias=alias,
                                          ComponentId=component_id,
                                          Role=role,
                                          HasActor=has_actor,
                                          DisplayName=display_name,
                                          )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShNode) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShNode:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtShNode:
        if "ShNodeId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ShNodeId")
        if "Alias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Alias")
        if "RoleGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing RoleGtEnumSymbol")
        d["Role"] = RoleMap.gt_to_local(d["RoleGtEnumSymbol"])
        if "ComponentId" not in d.keys():
            d["ComponentId"] = None
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None


        tuple = GtShNode(ShNodeId=d["ShNodeId"],                                    
                                          Alias=d["Alias"],
                                          ComponentId=d["ComponentId"],
                                          Role=d["Role"],
                                          HasActor=d["HasActor"],
                                          DisplayName=d["DisplayName"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtShNode) -> ShNode:
        s = {
            'sh_node_id': t.ShNodeId,
            'alias': t.Alias,
            'component_id': t.ComponentId,
            'has_actor': t.HasActor,
            'display_name': t.DisplayName,
            'role_gt_enum_symbol': RoleMap.local_to_gt(t.Role),}
        if s['sh_node_id'] in ShNode.by_id.keys():
            dc = ShNode.by_id[s['sh_node_id']]
        else:
            dc = ShNode(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ShNode) -> GtShNode:
        if dc is None:
            return None
        t = GtShNode(
             ShNodeId=dc.sh_node_id,
                                            Alias=dc.alias,
                                            ComponentId=dc.component_id,
                                            Role=dc.role,
                                            HasActor=dc.has_actor,
                                            DisplayName=dc.display_name,
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
