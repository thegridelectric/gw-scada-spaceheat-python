"""Makes gt.sh.node type"""

import json
from typing import Dict, Optional
from data_classes.sh_node import ShNode

from schema.gt.gt_sh_node.gt_sh_node import GtShNode
from schema.errors import MpSchemaError
from schema.enums.role.role_map import Role, RoleMap


class GtShNode_Maker():
    type_alias = 'gt.sh.node.100'

    def __init__(self,
                 sh_node_id: str,
                 alias: str,
                 role: Role,
                 primary_component_id: Optional[str],
                 display_name: Optional[str],
                 python_actor_name: Optional[str]):

        tuple = GtShNode(ShNodeId=sh_node_id,
                                          Alias=alias,
                                          PrimaryComponentId=primary_component_id,
                                          Role=role,
                                          DisplayName=display_name,
                                          PythonActorName=python_actor_name,
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
            raise MpSchemaError(f'Type must be string or bytes!')
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
        if "PrimaryComponentId" not in d.keys():
            d["PrimaryComponentId"] = None
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "PythonActorName" not in d.keys():
            d["PythonActorName"] = None

        tuple = GtShNode(ShNodeId=d["ShNodeId"],                                        
                                          Alias=d["Alias"],
                                          PrimaryComponentId=d["PrimaryComponentId"],
                                          Role=d["Role"],
                                          DisplayName=d["DisplayName"],
                                          PythonActorName=d["PythonActorName"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtShNode) -> ShNode:
        s = {
            'sh_node_id': t.ShNodeId,
            'alias': t.Alias,
            'primary_component_id': t.PrimaryComponentId,
            'display_name': t.DisplayName,
            'python_actor_name': t.PythonActorName,
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
            sShNodeId=dc.sh_node_id,
                                            Alias=dc.alias,
                                            PrimaryComponentId=dc.primary_component_id,
                                            Role=dc.role,
                                            DisplayName=dc.display_name,
                                            PythonActorName=dc.python_actor_name,
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
