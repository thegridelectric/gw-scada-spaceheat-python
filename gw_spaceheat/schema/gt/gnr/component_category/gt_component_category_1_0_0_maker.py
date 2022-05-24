"""Makes gt.component.category.100 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component_category import ComponentCategory
from schema.gt.gnr.component_category.gt_component_category_1_0_0 import GtComponentCategory100
    
    
class GtComponentCategory100_Maker():
    mp_alias = 'gt.component.category.100'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponentCategory100:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.category.100'
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponentCategory100(MpAlias=d["MpAlias"],
                        Value=d["Value"],
                        Description=d["Description"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:ComponentCategory) -> GtComponentCategory100:
        if dc is None:
            return None
        candidate = GtComponentCategory100(MpAlias='gt.component.category.100',
                        Value=dc.value,
                        Description=dc.description)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponentCategory100) -> ComponentCategory:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['value']=p.Value
        snake_dict['description']=p.Description
        if snake_dict['component_category_id'] in ComponentCategory.by_id.keys():
            component_category = ComponentCategory.by_id[snake_dict['component_category_id']]
            try:
                component_category.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning ComponentCategory: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning ComponentCategory: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component_category, key):
                    setattr(component_category, key, value)
        else:
            component_category = ComponentCategory(**snake_dict)

        return component_category

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 value: str,
                 description: str):
        self.errors = []

        t = GtComponentCategory100(MpAlias=GtComponentCategory100_Maker.mp_alias,
                    Value=value,
                    Description=description)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

