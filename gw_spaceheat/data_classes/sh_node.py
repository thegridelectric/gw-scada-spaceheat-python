"""ShNode definition"""
from typing import Dict, Optional

from data_classes.component import Component
from data_classes.errors import DataClassLoadingError
from enums import  RoleMap
from enums import  ActorClassMap, ActorClass


class ShNode:
    by_id: Dict[str, "ShNode"] = {}

    def __init__(
        self,
        sh_node_id: str,
        alias: str,
        actor_class_gt_enum_symbol: str,
        role_gt_enum_symbol: str,
        rated_voltage_v: Optional[int] = None,
        typical_voltage_v: Optional[int] = None,
        reporting_sample_period_s: Optional[int] = None,
        component_id: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        self.sh_node_id = sh_node_id
        self.alias = alias
        self.component_id = component_id
        self.reporting_sample_period_s = reporting_sample_period_s
        self.rated_voltage_v = rated_voltage_v
        self.typical_voltage_v = typical_voltage_v
        self.display_name = display_name
        self.actor_class = ActorClassMap.gt_to_local(actor_class_gt_enum_symbol)
        self.role = RoleMap.gt_to_local(role_gt_enum_symbol)

        ShNode.by_id[self.sh_node_id] = self

    def __repr__(self):
        rs = f"ShNode {self.display_name} => {self.role.value} {self.alias}, "
        if self.has_actor:
            rs += " (has actor)"
        else:
            rs += " (passive, no actor)"
        return rs

    @property
    def has_actor(self) -> bool:
        if self.actor_class == ActorClass.NoActor:
            return False
        return True

    @property
    def component(self) -> Optional[Component]:
        if self.component_id is None:
            return None
        if self.component_id not in Component.by_id.keys():
            raise DataClassLoadingError(f"{self.alias} component {self.component_id} not loaded!")
        return Component.by_id[self.component_id]
