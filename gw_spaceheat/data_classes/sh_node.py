"""ShNode definition"""
from typing import Dict, Optional

from data_classes.component import Component
from data_classes.errors import DataClassLoadingError
from enums import Role
from enums import ActorClass


class ShNode:
    by_id: Dict[str, "ShNode"] = {}

    def __init__(
        self,
        sh_node_id: str,
        alias: str,
        actor_class: ActorClass,
        role: Role,
        display_name: Optional[str] = None,
        component_id: Optional[str] = None,
        reporting_sample_period_s: Optional[int] = None,
        rated_voltage_v: Optional[int] = None,
        typical_voltage_v: Optional[int] = None,
        in_power_metering: Optional[bool] = None,
    ):
        self.sh_node_id = sh_node_id
        self.alias = alias
        self.actor_class = actor_class
        self.role = role
        self.display_name = display_name
        self.component_id = component_id
        self.reporting_sample_period_s = reporting_sample_period_s
        self.rated_voltage_v = rated_voltage_v
        self.typical_voltage_v = typical_voltage_v
        if in_power_metering:
            self.in_power_metering = in_power_metering
        else:
            self.in_power_metering = False
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
