"""Makes gt.component.attribute.class.200 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.component_type import ComponentType
from schema.gt.gnr.component_attribute_class.gt_component_attribute_class_2_0_0 import GtComponentAttributeClass200
from schema.gt.gnr.component_type.gt_component_type_1_0_0_maker import \
GtComponentType100_Maker, GtComponentType100
    
    
class GtComponentAttributeClass200_Maker():
    mp_alias = 'gt.component.attribute.class.200'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponentAttributeClass200:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.attribute.class.200'
        if 'ComponentType' not in d.keys():
            raise MpSchemaError("Missing required 'ComponentType' in gt.component.attribute.class.200 message")
        GtComponentType = GtComponentType100_Maker.camel_dict_to_schema_type(d["ComponentType"])
        if "RatedPowerWithdrawnVa" not in d.keys():
            d["RatedPowerWithdrawnVa"] = None
        if "SeriesReactanceOhms" not in d.keys():
            d["SeriesReactanceOhms"] = None 
        elif not d["SeriesReactanceOhms"] is None:
            d["SeriesReactanceOhms"] = float(d["SeriesReactanceOhms"])
        if "ResistanceOhms" not in d.keys():
            d["ResistanceOhms"] = None 
        elif not d["ResistanceOhms"] is None:
            d["ResistanceOhms"] = float(d["ResistanceOhms"])
        if "RatedPowerInjectedVa" not in d.keys():
            d["RatedPowerInjectedVa"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponentAttributeClass200(MpAlias=d["MpAlias"],
                        RatedPowerWithdrawnVa=d["RatedPowerWithdrawnVa"],
                        ComponentAttributeClassId=d["ComponentAttributeClassId"],
                        SeriesReactanceOhms=d["SeriesReactanceOhms"],
                        MakeModel=d["MakeModel"],
                        ResistanceOhms=d["ResistanceOhms"],
                        RatedPowerInjectedVa=d["RatedPowerInjectedVa"],
                        ComponentType=GtComponentType)
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:ComponentAttributeClass) -> GtComponentAttributeClass200:
        if dc is None:
            return None
        candidate = GtComponentAttributeClass200(MpAlias='gt.component.attribute.class.200',
                        RatedPowerWithdrawnVa=dc.rated_power_withdrawn_va,
                        ComponentAttributeClassId=dc.component_attribute_class_id,
                        SeriesReactanceOhms=dc.series_reactance_ohms,
                        MakeModel=dc.make_model,
                        ResistanceOhms=dc.resistance_ohms,
                        ComponentType=dc.component_type,
                        RatedPowerInjectedVa=dc.rated_power_injected_va)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponentAttributeClass200) -> ComponentAttributeClass:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['rated_power_withdrawn_va']=p.RatedPowerWithdrawnVa
        snake_dict['component_attribute_class_id']=p.ComponentAttributeClassId
        snake_dict['series_reactance_ohms']=p.SeriesReactanceOhms
        snake_dict['make_model']=p.MakeModel
        snake_dict['resistance_ohms']=p.ResistanceOhms
        snake_dict['component_type']=p.ComponentType
        snake_dict['rated_power_injected_va']=p.RatedPowerInjectedVa
        if snake_dict['component_attribute_class_id'] in ComponentAttributeClass.by_id.keys():
            component_attribute_class = ComponentAttributeClass.by_id[snake_dict['component_attribute_class_id']]
            try:
                component_attribute_class.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning ComponentAttributeClass: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning ComponentAttributeClass: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component_attribute_class, key):
                    setattr(component_attribute_class, key, value)
        else:
            component_attribute_class = ComponentAttributeClass(**snake_dict)

        return component_attribute_class

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: str,
                 component_type: ComponentType,
                 rated_power_withdrawn_va: Optional[int] = None ,
                 series_reactance_ohms: Optional[float] = None ,
                 resistance_ohms: Optional[float] = None ,
                 rated_power_injected_va: Optional[int] = None ):
        self.errors = []
        try:
            series_reactance_ohms = float(series_reactance_ohms)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            resistance_ohms = float(resistance_ohms)
        except ValueError:
            pass # This will get caught in is_valid() check below

        t = GtComponentAttributeClass200(MpAlias=GtComponentAttributeClass200_Maker.mp_alias,
                    RatedPowerWithdrawnVa=rated_power_withdrawn_va,
                    ComponentAttributeClassId=component_attribute_class_id,
                    SeriesReactanceOhms=series_reactance_ohms,
                    MakeModel=make_model,
                    ResistanceOhms=resistance_ohms,
                    RatedPowerInjectedVa=rated_power_injected_va,
                    ComponentType=Gt_Component_Type_1_0_0.payload_from_data_class(component_type))

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

