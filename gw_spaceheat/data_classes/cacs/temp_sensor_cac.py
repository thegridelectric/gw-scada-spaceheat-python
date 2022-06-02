""" TempSensorCac Class Definition """

from typing import Dict, Optional

from data_classes.cacs.sensor_cac import SensorCac
from data_classes.component_attribute_class import ComponentAttributeClass


class TempSensorCac(SensorCac):
    by_id: Dict[str, SensorCac] = {}

    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('display_name')
    base_props.append('sensor_type_value')
    base_props.append('comms_method')
    base_props.append('precision_exponent')
    base_props.append('temp_unit')

    def __new__(cls, component_attribute_class_id, *args, **kwargs):
        if component_attribute_class_id in ComponentAttributeClass.by_id.keys():
            if not isinstance(ComponentAttributeClass.by_id[component_attribute_class_id], cls):
                raise Exception(f"Id already exists for {ComponentAttributeClass.by_id[component_attribute_class_id]}"
                                ", not a temp sensor!")
            return ComponentAttributeClass.by_id[component_attribute_class_id]
        instance = super().__new__(cls, component_attribute_class_id=component_attribute_class_id)
        ComponentAttributeClass.by_id[component_attribute_class_id] = instance
        return instance

    def __init__(self,
                 component_attribute_class_id: Optional[str] = None,
                 sensor_type_value: Optional[str] = None,
                 make_model: Optional[str] = None,
                 display_name: Optional[str] = None,
                 comms_method: Optional[str] = None,
                 precision_exponent: Optional[int] = None,
                 temp_unit: Optional[str] = None):
        super(TempSensorCac, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                            make_model=make_model,
                                            display_name=display_name,
                                            sensor_type_value=sensor_type_value,
                                            comms_method=comms_method)
        self.precision_exponent = precision_exponent
        self.temp_unit = temp_unit

    def __repr__(self):
        val = f'TempSensorCac {self.make_model}: {self.display_name}'
        if self.comms_method:
            val += f', Comms method: {self.comms_method}'
        if self.precision_exponent:
            val += f', Precision exponent: {self.precision_exponent}'
        if self.temp_unit:
            val += f', Temp unit: {self.temp_unit}'
        return val
    