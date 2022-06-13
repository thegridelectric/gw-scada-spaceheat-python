"""ShNode definition"""
from typing import Dict, List, Optional

from data_classes.component import Component
from data_classes.errors import DataClassLoadingError
from data_classes.sh_node_base import ShNodeBase
from schema.gt.gt_sh_node.gt_sh_node import GtShNode


class ShNode(ShNodeBase):
    by_id: Dict[str, ShNodeBase] = ShNodeBase._by_id
    by_alias: Dict[str, ShNodeBase] = {}

    def __init__(self, sh_node_id: str,
                 alias: str,
                 python_actor_name: str,
                 role_gt_enum_symbol: str,
                 primary_component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(sh_node_id=sh_node_id,
                                             alias=alias,
                                             primary_component_id=primary_component_id,
                                             display_name=display_name,
                                             python_actor_name=python_actor_name,
                                             role_gt_enum_symbol=role_gt_enum_symbol,
                                             )
        ShNode.by_alias[self.alias] = self

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
    def primary_component(self) -> Optional[Component]:
        if self.primary_component_id is None:
            return None
        if self.primary_component_id not in Component.by_id.keys():
            raise DataClassLoadingError(f"{self.alias} primary component {self.primary_component_id} not loaded!")
        return Component.by_id[self.primary_component_id]

    @property
    def parent(self) -> ShNodeBase:
        alias_list = self.alias.split(".")
        alias_list.pop()
        if len(alias_list) == 0:
            return None
        else:
            parent_alias = ".".join(alias_list)
            return ShNode.by_alias[parent_alias]

    @property
    def descendants(self) -> List[ShNodeBase]:
        return list(filter(lambda x: x.alias.startswith(self.alias), ShNode.by_alias.values()))
    
    @property
    def has_actor(self) -> bool:
        if self.python_actor_name is None:
            return False
        return True