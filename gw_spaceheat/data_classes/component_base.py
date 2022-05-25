""" Component Base Class Definition """
import time
import uuid
from typing import Optional
from abc import ABC, abstractproperty
from gw.mixin import StreamlinedSerializerMixin


class ComponentBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('static_space_heat_thermostat_setpoint_f')
    base_props.append('annual_hvac_kwh_th_ymd')
    base_props.append('zero_heat_delta_f')
    base_props.append('g_node_id')
    base_props.append('ymd_weather_uid')
    base_props.append('mixing_valve_temp_f')
    base_props.append('heat_capacity_wh_per_deg_f')
    base_props.append('component_attribute_class_id')

    def __new__(cls, component_id, *args, **kwargs):
        try:
            return cls.by_id[component_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[component_id] = instance
            return instance

    def __init__(self,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 static_space_heat_thermostat_setpoint_f: Optional[float] = None,
                 annual_hvac_kwh_th_ymd: Optional[int] = None,
                 zero_heat_delta_f: Optional[int] = None,
                 g_node_id: Optional[str] = None,
                 ymd_weather_uid: Optional[str] = None,
                 mixing_valve_temp_f: Optional[int] = None,
                 heat_capacity_wh_per_deg_f: Optional[int] = None,
                 component_attribute_class_id: Optional[str] = None):
        self.component_id = component_id
        self.display_name = display_name
        if static_space_heat_thermostat_setpoint_f:
            self.static_space_heat_thermostat_setpoint_f = float(static_space_heat_thermostat_setpoint_f)
        else:
            self.static_space_heat_thermostat_setpoint_f = None
        self.annual_hvac_kwh_th_ymd = annual_hvac_kwh_th_ymd
        self.zero_heat_delta_f = zero_heat_delta_f
        self.g_node_id = g_node_id
        self.ymd_weather_uid = ymd_weather_uid
        self.mixing_valve_temp_f = mixing_valve_temp_f
        self.heat_capacity_wh_per_deg_f = heat_capacity_wh_per_deg_f
        self.component_attribute_class_id = component_attribute_class_id

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_id'] in cls.by_id.keys():
            raise Exception(f"component_id {attributes['component_id']} already in use")


    """ Derived attributes """

    @abstractproperty
    def registry_name(self):
        """From Airtable Axioms:  """
        raise NotImplementedError
