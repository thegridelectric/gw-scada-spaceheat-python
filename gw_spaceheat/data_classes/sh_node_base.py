"""ShNodeBase definition"""

from abc import ABC, abstractmethod
from typing import Optional

from schema.gt.gt_sh_node.gt_sh_node import GtShNode
from data_classes.errors import DcError
from schema.enums.role.role_map import RoleMap


class ShNodeBase(ABC):
    base_props = []
    base_props.append("sh_node_id")
    base_props.append("alias")
    base_props.append("component_id")
    base_props.append("display_name")
    base_props.append("has_actor")
    base_props.append("role_gt_enum_symbol")

    def __init__(self,
                 sh_node_id: str,
                 alias: str,
                 role_gt_enum_symbol: str,
                 has_actor: bool,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        self.sh_node_id = sh_node_id
        self.alias = alias
        self.component_id = component_id
        self.display_name = display_name
        self.has_actor = has_actor
        self.role = RoleMap.gt_to_local(role_gt_enum_symbol)

    def update(self, type: GtShNode):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtShNode):
        if self.role != type.Role:
            raise DcError(f'role must be immutable for {self}. '
                          f'Got {type.Role}')

    @abstractmethod
    def _check_update_axioms(self, type: GtShNode):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
