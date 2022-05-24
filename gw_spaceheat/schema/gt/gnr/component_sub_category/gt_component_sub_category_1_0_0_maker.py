"""Makes gt.component.sub.category.100 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component_sub_category import ComponentSubCategory
from data_classes.component_category import ComponentCategory
from schema.gt.gnr.component_sub_category.gt_component_sub_category_1_0_0 import GtComponentSubCategory100
from schema.gt.gnr.component_category.gt_component_category_1_0_0_maker import \
GtComponentCategory100_Maker, GtComponentCategory100
    
    
class GtComponentSubCategory100_Maker():
    mp_alias = 'gt.component.sub.category.100'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponentSubCategory100:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.sub.category.100'
        if 'ComponentCategory' not in d.keys():
            raise MpSchemaError("Missing required 'ComponentCategory' in gt.component.sub.category.100 message")
        GtComponentCategory = GtComponentCategory100_Maker.camel_dict_to_schema_type(d["ComponentCategory"])
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponentSubCategory100(MpAlias=d["MpAlias"],
                        Value=d["Value"],
                        ComponentCategory=GtComponentCategory)
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:ComponentSubCategory) -> GtComponentSubCategory100:
        if dc is None:
            return None
        candidate = GtComponentSubCategory100(MpAlias='gt.component.sub.category.100',
                        Value=dc.value,
                        ComponentCategory=dc.component_category)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponentSubCategory100) -> ComponentSubCategory:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['value']=p.Value
        snake_dict['component_category']=p.ComponentCategory
        if snake_dict['component_sub_category_id'] in ComponentSubCategory.by_id.keys():
            component_sub_category = ComponentSubCategory.by_id[snake_dict['component_sub_category_id']]
            try:
                component_sub_category.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning ComponentSubCategory: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning ComponentSubCategory: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component_sub_category, key):
                    setattr(component_sub_category, key, value)
        else:
            component_sub_category = ComponentSubCategory(**snake_dict)

        return component_sub_category

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
                 component_category: ComponentCategory):
        self.errors = []

        t = GtComponentSubCategory100(MpAlias=GtComponentSubCategory100_maker.mp_alias,
                    Value=value,
                    ComponentCategory=Gt_Component_Category_1_0_0.payload_from_data_class(component_category))

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

