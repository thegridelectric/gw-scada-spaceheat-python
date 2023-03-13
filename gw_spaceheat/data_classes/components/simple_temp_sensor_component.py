"""SimpleTempSensorComponent definition"""
from typing import Dict, Optional

from data_classes.cacs.simple_temp_sensor_cac import SimpleTempSensorCac
from data_classes.component import Component
from enums import MakeModel


class SimpleTempSensorComponent(Component):
    by_id: Dict[str, "SimpleTempSensorComponent"] = {}

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str] = None,
        hw_uid: Optional[str] = None,
        channel: Optional[int] = None,
    ):
        super(self.__class__, self).__init__(
            display_name=display_name,
            component_id=component_id,
            hw_uid=hw_uid,
            component_attribute_class_id=component_attribute_class_id,
        )
        self.channel: Optional[int] = channel
        SimpleTempSensorComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self


    @property
    def cac(self) -> SimpleTempSensorCac:
        return SimpleTempSensorCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
