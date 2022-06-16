"""ShNode definition"""
from typing import Dict, List, Optional

from data_classes.component import Component
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.errors import DataClassLoadingError
from data_classes.sh_node_base import ShNodeBase
from schema.gt.gt_sh_node.gt_sh_node import GtShNode


class ShNode(ShNodeBase):
    by_id: Dict[str, "ShNode"] = {}
    by_alias: Dict[str, "ShNode"] = {}

    def __init__(self, sh_node_id: str,
                 alias: str,
                 has_actor: bool,
                 role_gt_enum_symbol: str,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(sh_node_id=sh_node_id,
                                             alias=alias,
                                             has_actor=has_actor,
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
