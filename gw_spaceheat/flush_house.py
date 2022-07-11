from data_classes.components.boolean_actuator_component import (
    BooleanActuatorComponent,
    BooleanActuatorCac,
)
from data_classes.components.electric_meter_component import (
    ElectricMeterComponent,
    ElectricMeterCac,
)
from data_classes.components.pipe_flow_sensor_component import (
    PipeFlowSensorComponent,
    PipeFlowSensorCac,
)
from data_classes.components.resistive_heater_component import (
    ResistiveHeaterComponent,
    ResistiveHeaterCac,
)
from data_classes.components.temp_sensor_component import TempSensorComponent, TempSensorCac

from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.sh_node import ShNode


def flush_components():
    BooleanActuatorComponent.by_id = {}
    ElectricMeterComponent.by_id = {}
    PipeFlowSensorComponent.by_id = {}
    ResistiveHeaterComponent.by_id = {}
    TempSensorComponent.by_id = {}
    Component.by_id = {}


def flush_cacs():
    BooleanActuatorCac.by_id = {}
    ElectricMeterCac.by_id = {}
    PipeFlowSensorCac.by_id = {}
    ResistiveHeaterCac.by_id = {}
    TempSensorCac.by_id = {}
    ComponentAttributeClass.by_id = {}


def flush_spaceheat_nodes():
    ShNode.by_id = {}
    ShNode.by_alias = {}


def flush_all():
    flush_components()
    flush_cacs()
    flush_spaceheat_nodes()
