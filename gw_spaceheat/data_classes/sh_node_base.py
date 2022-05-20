""" ShNode Base Class Definition """

from typing import Optional
from abc import ABC, abstractproperty
from typing import List
from data_classes.mixin import StreamlinedSerializerMixin


class ShNodeBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    base_props = []
    base_props.append('sh_node_id')
    base_props.append('alias')
    base_props.append('sh_node_role_alias')
    base_props.append('display_name')
    base_props.append('primary_component_id')
    base_props.append('has_python_actor')

    def __new__(cls, sh_node_id, *args, **kwargs):
        try:
            return cls.by_id[sh_node_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[sh_node_id] = instance
            return instance

    def __init__(self,
                 sh_node_id: Optional[str] = None,
                 alias: Optional[str] = None,
                 sh_node_role_alias: Optional[str] = None,
                 display_name: Optional[str] = None,
                 primary_component_id: Optional[str] = None,
                 python_actor_name: Optional[str] = None
                 ):
        self.sh_node_id = sh_node_id
        self.alias = alias
        self.sh_node_role_alias = sh_node_role_alias
        self.display_name = display_name
        self.primary_component_id = primary_component_id
        self.python_actor_name = python_actor_name

            
    def __repr__(self):
        rs =  f'HouseNode {self.display_name} => Alias: {self.alias}'
        #if self.primary_component:
        return rs


    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['sh_node_id'] in cls.by_id.keys():
            raise Exception(f"sh_node_id {attributes['sh_node_id']} already in use")

    """ Derived attributes """

    @abstractproperty
    def parent(self):
        """From Airtable Axioms: Parent is determined by tree structure of alias, and exists for all GNodes 
        with at least one separator. I.e. If gNode.alias = "sw1.ne.bf1" then the 
        Parent GNode must exist and have alias "sw1.ne".   If Parent does not exist 
        then request information from GNodeRegistry.  """
        raise NotImplementedError

