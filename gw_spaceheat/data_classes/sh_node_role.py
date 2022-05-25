""" ShNodeRole Definition """

from abc import ABC
from typing import Optional

from data_classes.mixin import StreamlinedSerializerMixin


class ShNodeRole(ABC, StreamlinedSerializerMixin):
    by_alias = {}
    
    base_props = []
    base_props.append('alias')
    base_props.append('has_heat_flow')
    base_props.append('has_voltage')
    base_props.append('has_stored_thermal_energy')
    base_props.append('is_actuated')

    def __new__(cls, alias, *args, **kwargs):
        try:
            return cls.by_alias[alias]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_alias[alias] = instance
            return instance

    def __init__(self,
                 alias: Optional[str] = None,
                 has_heat_flow: Optional[bool] = None,
                 has_voltage: Optional[bool] = None,
                 has_stored_thermal_energy: Optional[bool] = None,
                 is_actuated: Optional[bool] = None):
        self.alias = alias
        self.has_heat_flow = has_heat_flow
        self.has_voltage = has_voltage
        self.has_stored_thermal_energy = has_stored_thermal_energy
        self.is_actuated = is_actuated

    def __repr__(self):
        return f"ShNodeRole {self.alias}: HasVoltage {self.has_stored_thermal_energy}, HasHeatFlow {self.has_heat_flow}, HasStoredThermalEnergy {self.has_stored_thermal_energy}"
