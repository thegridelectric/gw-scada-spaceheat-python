import time

from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.components.boolean_actuator_component import BooleanActuatorCac
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.components.electric_meter_component import ElectricMeterCac
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorCac
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorCac
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from data_classes.components.resistive_heater_component import ResistiveHeaterCac
from data_classes.components.resistive_heater_component import ResistiveHeaterComponent
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorCac
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from data_classes.sh_node import ShNode

from tests.utils.scada_recorder import ScadaRecorder
from tests.utils.wait import wait_for
from tests.utils.wait import await_for
from tests.utils.wait import AwaitablePredicate
from tests.utils.wait import Predicate
from tests.utils.wait import ErrorStringFunction

def flush_components():
    BooleanActuatorComponent.by_id = {}
    ElectricMeterComponent.by_id = {}
    PipeFlowSensorComponent.by_id = {}
    MultipurposeSensorComponent.by_id = {}
    ResistiveHeaterComponent.by_id = {}
    SimpleTempSensorComponent.by_id = {}
    Component.by_id = {}


def flush_cacs():
    BooleanActuatorCac.by_id = {}
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


class StopWatch(object):
    """Measure time with context manager"""

    start: float = 0
    end: float = 0
    elapsed: float = 0

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type_, value, traceback):
        self.end = time.time()
        self.elapsed = self.end - self.start
