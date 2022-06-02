from typing import Optional

from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.component import Component
from data_classes.components.sensor_component import SensorComponent
from data_classes.errors import DataClassLoadingError


class TempSensorComponent(SensorComponent):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('component_attribute_class_id')
    base_props.append('hw_uid')

    def __new__(cls, component_id, *args, **kwargs):
        if component_id in Component.by_id.keys():
            if not isinstance(Component.by_id[component_id], cls):
                raise Exception("Id already exists, not a temp sensor!")
            return Component.by_id[component_id]
        instance = super().__new__(cls, component_id=component_id)
        Component.by_id[component_id] = instance
        return instance

    def __init__(self,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 component_attribute_class_id: Optional[str] = None,
                 hw_uid: Optional[str] = None):
        super(TempSensorComponent, self).__init__(component_id=component_id,
                                                  display_name=display_name,
                                                  component_attribute_class_id=component_attribute_class_id,
                                                  hw_uid=hw_uid)

    @classmethod
    def check_initialization_consistency(cls, attributes):
        SensorComponent.check_uniqueness_of_primary_key(attributes)
        SensorComponent.check_existence_of_certain_attributes(attributes)

    @property
    def cac(self) -> TempSensorCac:
        if self.component_attribute_class_id not in TempSensorCac.by_id.keys():
            raise DataClassLoadingError(f"TempSensorCacId {self.component_attribute_class_id} not loaded yet")
        return TempSensorCac.by_id[self.component_attribute_class_id]