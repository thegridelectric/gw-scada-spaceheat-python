"""Makes gt.component.type.100 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component_type import ComponentType
from data_classes.component_sub_category import ComponentSubCategory
from schema.gt.gnr.component_type.gt_component_type_1_0_0 import GtComponentType100
from schema.gt.gnr.component_sub_category.gt_component_sub_category_1_0_0_maker import \
GtComponentSubCategory100_Maker, GtComponentSubCategory100
    
    
class GtComponentType100_Maker():
    mp_alias = 'gt.component.type.1_0_0'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponentType100:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.type.100'
        if 'ComponentSubCategory' not in d.keys():
            raise MpSchemaError("Missing required 'ComponentSubCategory' in gt.component.type.100 message")
        GtComponentSubCategory = GtComponentSubCategory100_Maker.camel_dict_to_schema_type(d["ComponentSubCategory"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "ExpectedShutdownSeconds" not in d.keys():
            d["ExpectedShutdownSeconds"] = None
        if "ExpectedStartupSeconds" not in d.keys():
            d["ExpectedStartupSeconds"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponentType100(MpAlias=d["MpAlias"],
                        IsResistiveLoad=d["IsResistiveLoad"],
                        DisplayName=d["DisplayName"],
                        ExpectedShutdownSeconds=d["ExpectedShutdownSeconds"],
                        Value=d["Value"],
                        ExpectedStartupSeconds=d["ExpectedStartupSeconds"],
                        ComponentSubCategory=GtComponentSubCategory)
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:ComponentType) -> GtComponentType100:
        if dc is None:
            return None
        candidate = GtComponentType100(MpAlias='gt.component.type.100',
                        IsResistiveLoad=dc.is_resistive_load,
                        DisplayName=dc.display_name,
                        ExpectedShutdownSeconds=dc.expected_shutdown_seconds,
                        Value=dc.value,
                        ComponentSubCategory=dc.component_sub_category,
                        ExpectedStartupSeconds=dc.expected_startup_seconds)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponentType100) -> ComponentType:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['is_resistive_load']=p.IsResistiveLoad
        snake_dict['display_name']=p.DisplayName
        snake_dict['expected_shutdown_seconds']=p.ExpectedShutdownSeconds
        snake_dict['value']=p.Value
        snake_dict['component_sub_category']=p.ComponentSubCategory
        snake_dict['expected_startup_seconds']=p.ExpectedStartupSeconds
        if snake_dict['component_type_id'] in ComponentType.by_id.keys():
            component_type = ComponentType.by_id[snake_dict['component_type_id']]
            try:
                component_type.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning ComponentType: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning ComponentType: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component_type, key):
                    setattr(component_type, key, value)
        else:
            component_type = ComponentType(**snake_dict)

        return component_type

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 is_resistive_load: bool,
                 value: str,
                 component_sub_category: ComponentSubCategory,
                 display_name: Optional[str] = None ,
                 expected_shutdown_seconds: Optional[int] = None ,
                 expected_startup_seconds: Optional[int] = None ):
        self.errors = []

        t = GtComponentType100(MpAlias=GtComponentType100_maker.mp_alias,
                    IsResistiveLoad=is_resistive_load,
                    DisplayName=display_name,
                    ExpectedShutdownSeconds=expected_shutdown_seconds,
                    Value=value,
                    ExpectedStartupSeconds=expected_startup_seconds,
                    ComponentSubCategory=Gt_Component_Sub_Category_1_0_0.payload_from_data_class(component_sub_category))

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

