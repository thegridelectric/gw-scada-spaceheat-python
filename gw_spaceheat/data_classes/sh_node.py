"""ShNode definition"""
from typing import Dict, List, Optional

from data_classes.component import Component
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.errors import DataClassLoadingError
from data_classes.sh_node_base import ShNodeBase
from schema.gt.gt_sh_node.gt_sh_node import GtShNode
from schema.enums.actor_class.actor_class_map import ActorClass


class ShNode(ShNodeBase):
    by_id: Dict[str, "ShNode"] = {}
    by_alias: Dict[str, "ShNode"] = {}

    def __init__(self, sh_node_id: str,
                 alias: str,
                 actor_class_gt_enum_symbol: str,
                 role_gt_enum_symbol: str,
                 reporting_sample_period_s: Optional[int] = None,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(sh_node_id=sh_node_id,
                                             alias=alias,
                                             actor_class_gt_enum_symbol=actor_class_gt_enum_symbol,
                                             reporting_sample_period_s=reporting_sample_period_s,
                                             component_id=component_id,
                                             display_name=display_name,
                                             role_gt_enum_symbol=role_gt_enum_symbol,
                                             )

        ShNode.by_alias[self.alias] = self
        ShNode.by_id[self.sh_node_id] = self

    def _check_update_axioms(self, type: GtShNode):
        pass

    def __repr__(self):
        rs = f'ShNode {self.display_name} => {self.role.value} {self.alias}, '
        if self.has_actor:
            rs += ' (has actor)'
        else:
            rs += ' (passive, no actor)'
        return rs

    @property
    def has_actor(self) -> bool:
        if self.actor_class == ActorClass.NONE:
            return False
        return True

    @property
    def component(self) -> Optional[Component]:
        if self.component_id is None:
            return None
        if self.component_id not in Component.by_id.keys():
            raise DataClassLoadingError(f"{self.alias} component {self.component_id} not loaded!")
        return Component.by_id[self.component_id]

    @property
    def temp_sensor_component(self) -> Optional[TempSensorComponent]:
        if self.component_id is None:
            return None
        if self.component_id not in Component.by_id.keys():
            raise DataClassLoadingError(f"{self.alias}  component {self.component_id} not loaded!")
        if self.component_id not in TempSensorComponent.by_id.keys():
            return None
        return TempSensorComponent.by_id[self.component_id]

    @property
    def parent(self) -> "ShNode":
        alias_list = self.alias.split(".")
        alias_list.pop()
        if len(alias_list) == 0:
            return None
        else:
            parent_alias = ".".join(alias_list)
            if parent_alias not in ShNode.by_alias.keys():
                raise DataClassLoadingError(f"{self.alias} is missing parent {parent_alias}!")
            return ShNode.by_alias[parent_alias]

    @property
    def descendants(self) -> List["ShNode"]:
        return list(filter(lambda x: x.alias.startswith(self.alias), ShNode.by_alias.values()))
