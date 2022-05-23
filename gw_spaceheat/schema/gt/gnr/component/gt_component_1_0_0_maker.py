"""Makes gt.component.100 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component import Component
from schema.gt.gnr.component.gt_component_1_0_0 import GtComponent100
    
    
class GtComponent100_Maker():
    mp_alias = 'gt.component.1_0_0'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponent100:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.100'
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponent100(MpAlias=d["MpAlias"],
                        DisplayName=d["DisplayName"],
                        ComponentId=d["ComponentId"],
                        ComponentAttributeClassId=d["ComponentAttributeClassId"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:Component) -> GtComponent100:
        if dc is None:
            return None
        candidate = GtComponent100(MpAlias='gt.component.100',
                        DisplayName=dc.display_name,
                        ComponentId=dc.component_id,
                        ComponentAttributeClassId=dc.component_attribute_class_id)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponent100) -> Component:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['display_name']=p.DisplayName
        snake_dict['component_id']=p.ComponentId
        snake_dict['component_attribute_class_id']=p.ComponentAttributeClassId
        if snake_dict['component_id'] in Component.by_id.keys():
            component = Component.by_id[snake_dict['component_id']]
            try:
                component.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning Component: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning Component: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component, key):
                    setattr(component, key, value)
        else:
            component = Component(**snake_dict)

        return component

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 display_name: str,
                 component_id: str,
                 component_attribute_class_id: str):
        self.errors = []

        t = GtComponent100(MpAlias=GtComponent100_maker.mp_alias,
                    DisplayName=display_name,
                    ComponentId=component_id,
                    ComponentAttributeClassId=component_attribute_class_id)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

