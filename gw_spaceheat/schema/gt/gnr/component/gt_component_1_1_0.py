"""TypeMaker for gt.component.1_1_0"""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component import Component
from schema.gt.gnr.component.gt_component_1_1_0_schema import GtComponent110
    
    
class Gt_Component_1_1_0():
    mp_alias = 'gt.component.1_1_0'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponent110:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.1_1_0'
        if "YmdWeatherUid" not in d.keys():
            d["YmdWeatherUid"] = None
        if "AnnualHvacKwhThYmd" not in d.keys():
            d["AnnualHvacKwhThYmd"] = None
        if "GNodeId" not in d.keys():
            d["GNodeId"] = None
        if "HeatCapacityWhPerDegF" not in d.keys():
            d["HeatCapacityWhPerDegF"] = None
        if "StaticSpaceHeatThermostatSetpointF" not in d.keys():
            d["StaticSpaceHeatThermostatSetpointF"] = None 
        elif not d["StaticSpaceHeatThermostatSetpointF"] is None:
            d["StaticSpaceHeatThermostatSetpointF"] = float(d["StaticSpaceHeatThermostatSetpointF"])
        if "ZeroHeatDeltaF" not in d.keys():
            d["ZeroHeatDeltaF"] = None
        if "MixingValveTempF" not in d.keys():
            d["MixingValveTempF"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponent110(MpAlias=d["MpAlias"],
                        ComponentId=d["ComponentId"],
                        DisplayName=d["DisplayName"],
                        YmdWeatherUid=d["YmdWeatherUid"],
                        ComponentAttributeClassId=d["ComponentAttributeClassId"],
                        AnnualHvacKwhThYmd=d["AnnualHvacKwhThYmd"],
                        GNodeId=d["GNodeId"],
                        HeatCapacityWhPerDegF=d["HeatCapacityWhPerDegF"],
                        StaticSpaceHeatThermostatSetpointF=d["StaticSpaceHeatThermostatSetpointF"],
                        ZeroHeatDeltaF=d["ZeroHeatDeltaF"],
                        MixingValveTempF=d["MixingValveTempF"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:Component) -> GtComponent110:
        if dc is None:
            return None
        candidate = GtComponent110(MpAlias='gt.component.1_1_0',
                        ComponentId=dc.component_id,
                        DisplayName=dc.display_name,
                        YmdWeatherUid=dc.ymd_weather_uid,
                        ComponentAttributeClassId=dc.component_attribute_class_id,
                        AnnualHvacKwhThYmd=dc.annual_hvac_kwh_th_ymd,
                        GNodeId=dc.g_node_id,
                        HeatCapacityWhPerDegF=dc.heat_capacity_wh_per_deg_f,
                        StaticSpaceHeatThermostatSetpointF=dc.static_space_heat_thermostat_setpoint_f,
                        ZeroHeatDeltaF=dc.zero_heat_delta_f,
                        MixingValveTempF=dc.mixing_valve_temp_f)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponent110) -> Component:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['component_id']=p.ComponentId
        snake_dict['display_name']=p.DisplayName
        snake_dict['ymd_weather_uid']=p.YmdWeatherUid
        snake_dict['component_attribute_class_id']=p.ComponentAttributeClassId
        snake_dict['annual_hvac_kwh_th_ymd']=p.AnnualHvacKwhThYmd
        snake_dict['g_node_id']=p.GNodeId
        snake_dict['heat_capacity_wh_per_deg_f']=p.HeatCapacityWhPerDegF
        snake_dict['static_space_heat_thermostat_setpoint_f']=p.StaticSpaceHeatThermostatSetpointF
        snake_dict['zero_heat_delta_f']=p.ZeroHeatDeltaF
        snake_dict['mixing_valve_temp_f']=p.MixingValveTempF
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
    def type_is_valid(cls, payload_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(payload_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 component_id: str,
                 display_name: str,
                 component_attribute_class_id: str,
                 ymd_weather_uid: Optional[str] = None ,
                 annual_hvac_kwh_th_ymd: Optional[int] = None ,
                 g_node_id: Optional[str] = None ,
                 heat_capacity_wh_per_deg_f: Optional[int] = None ,
                 static_space_heat_thermostat_setpoint_f: Optional[float] = None ,
                 zero_heat_delta_f: Optional[int] = None ,
                 mixing_valve_temp_f: Optional[int] = None ):
        self.errors = []
        try:
            static_space_heat_thermostat_setpoint_f = float(static_space_heat_thermostat_setpoint_f)
        except ValueError:
            pass # This will get caught in is_valid() check below

        t = GtComponent110(MpAlias=Gt_Component_1_1_0.mp_alias,
                    ComponentId=component_id,
                    DisplayName=display_name,
                    YmdWeatherUid=ymd_weather_uid,
                    ComponentAttributeClassId=component_attribute_class_id,
                    AnnualHvacKwhThYmd=annual_hvac_kwh_th_ymd,
                    GNodeId=g_node_id,
                    HeatCapacityWhPerDegF=heat_capacity_wh_per_deg_f,
                    StaticSpaceHeatThermostatSetpointF=static_space_heat_thermostat_setpoint_f,
                    ZeroHeatDeltaF=zero_heat_delta_f,
                    MixingValveTempF=mixing_valve_temp_f)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

