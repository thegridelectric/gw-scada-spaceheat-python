from gwproto.data_classes.component import Component
from gwproto.data_classes.component_attribute_class import ComponentAttributeClass
from gwproto.data_classes.components.relay_component import RelayCac
from gwproto.data_classes.components.relay_component import RelayComponent
from gwproto.data_classes.components.electric_meter_component import ElectricMeterCac
from gwproto.data_classes.components.electric_meter_component import ElectricMeterComponent
from gwproto.data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from gwproto.data_classes.components.multipurpose_sensor_component import MultipurposeSensorCac
from gwproto.data_classes.components.pipe_flow_sensor_component import PipeFlowSensorCac
from gwproto.data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from gwproto.data_classes.components.resistive_heater_component import ResistiveHeaterCac
from gwproto.data_classes.components.resistive_heater_component import ResistiveHeaterComponent
from gwproto.data_classes.components.simple_temp_sensor_component import SimpleTempSensorCac
from gwproto.data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from gwproto.data_classes.sh_node import ShNode

from tests.utils.scada_recorder import ScadaRecorder

def flush_components():
    RelayComponent.by_id = {}
    ElectricMeterComponent.by_id = {}
    PipeFlowSensorComponent.by_id = {}
    MultipurposeSensorComponent.by_id = {}
    ResistiveHeaterComponent.by_id = {}
    SimpleTempSensorComponent.by_id = {}
    Component.by_id = {}


def flush_cacs():
    RelayCac.by_id = {}
    ElectricMeterCac.by_id = {}
    MultipurposeSensorCac.by_id = {}
    PipeFlowSensorCac.by_id = {}
    ResistiveHeaterCac.by_id = {}
    SimpleTempSensorCac.by_id = {}
    ComponentAttributeClass.by_id = {}


def flush_spaceheat_nodes():
    ShNode.by_id = {}


def flush_all():
    flush_components()
    flush_cacs()
    flush_spaceheat_nodes()

