""" ShNode Class Definition"""
from typing import Dict, List, Optional

from data_classes.component import Component
from data_classes.components.electric_heater_component import \
    ElectricHeaterComponent
from data_classes.errors import DataClassLoadingError, DcError
from data_classes.sh_node_base import ShNodeBase
from data_classes.sh_node_role import ShNodeRole
from data_classes.sh_node_role_static import (ELECTRIC_HEATER,
                                              PlatformShNodeRole)


class ShNode(ShNodeBase):
    by_alias: Dict[str, ShNodeBase] = {}

    def __init__(self,
                 sh_node_id: Optional[str] = None,
                 alias: Optional[str] = None,
                 sh_node_role_alias: Optional[str] = None,
                 display_name: Optional[str] = None,
                 primary_component_id: Optional[str] = None,
                 python_actor_name: Optional[str] = None
                 ):
        super(ShNode, self).__init__(sh_node_id=sh_node_id,
                alias=alias,
                sh_node_role_alias=sh_node_role_alias,
                display_name=display_name,
                primary_component_id=primary_component_id,
                python_actor_name=python_actor_name)
        self.__class__.by_alias[self.alias] = self

    def __repr__(self):
        rs =  f'ShNode {self.display_name} => {self.sh_node_role.alias} {self.alias}, '
        if self.has_actor:
            rs += ' (has actor)'
        else:
            rs += ' (passive, no actor)'
        return rs

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes: Dict):
        if not attributes.get('sh_node_id', None):
            raise DcError('sh_node_id must exist')
        if not attributes.get('alias', None):
            raise DcError('alias must exist')
        if not attributes.get('display_name', None):
            raise DcError('display_name must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ShNode.check_uniqueness_of_primary_key(attributes)
        ShNode.check_existence_of_certain_attributes(attributes)

    def check_immutability_for_existing_attributes(self, new_attributes):
        if self.sh_node_id:
            if new_attributes['sh_node_id'] != self.sh_node_id:
                raise DcError('sh_node_id is Immutable')
            if self.primary_component_id and 'primary_component_id' in new_attributes.keys():
                if self.sh_node_role == ELECTRIC_HEATER:
                    try:
                        new_component = ElectricHeaterComponent.by_id[new_attributes['primary_component_id']]
                        self.primary_component
                    except (KeyError, DataClassLoadingError) as err:
                        raise DataClassLoadingError(f"Component for GNode {self.alias} is changing! Component with "
                                                    f"id {new_attributes['primary_component_id']} must"
                                                    f"be loaded before this action is done, in order to validate that "
                                                    f"the ComponentAttributeClass remains the same ")
                    if self.primary_component.electric_heater_cac != new_component.electric_heater_cac:
                        raise DcError(f"component attribute class for {self.alias} cannot change! Attempt to change "
                                                f"from class {self.primary_component.electric_heater_cac} to"
                                                f" {new_component.electric_heater_cac}")




    @property
    def sh_node_role(self) -> ShNodeRole:
        if not self.sh_node_role_alias in PlatformShNodeRole.keys():
            raise TypeError(f'ShNodeRole {self.sh_node_role_alias} for {self.alias} must belong to static list')
        return PlatformShNodeRole[self.sh_node_role_alias]
        
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