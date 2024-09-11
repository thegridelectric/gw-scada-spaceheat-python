from gwproto.data_classes.component import Component
from gwproto.data_classes.components.relay_component import RelayComponent
from gwproto.data_classes.components.electric_meter_component import ElectricMeterComponent
from gwproto.data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from gwproto.data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from gwproto.data_classes.components.resistive_heater_component import ResistiveHeaterComponent
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


def flush_spaceheat_nodes():
    ShNode.by_id = {}


def flush_all():
    flush_components()
    flush_spaceheat_nodes()

