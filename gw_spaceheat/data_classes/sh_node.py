"""ShNode definition"""
from typing import Dict, Optional

from data_classes.sh_node_base import ShNodeBase
from schema.gt.gt_sh_node.gt_sh_node import GtShNode


class ShNode(ShNodeBase):
    by_id: Dict[str, ShNodeBase] = ShNodeBase._by_id

    def __init__(self, sh_node_id: str,
                 alias: str,
                 role_gt_enum_symbol: str,
                 primary_component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 python_actor_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(sh_node_id=sh_node_id,
                                             alias=alias,
                                             primary_component_id=primary_component_id,
                                             display_name=display_name,
                                             python_actor_name=python_actor_name,
                                             role_gt_enum_symbol=role_gt_enum_symbol,
                                             )

    def _check_update_axioms(self, type: GtShNode):
        pass

    def __repr__(self):
        return f"{self.sh_node_id}"
