from data_classes.sh_node import ShNode
from schema.enums.actor_class.actor_class_map import ActorClass

from actors.atn import Atn
from actors.boolean_actuator import BooleanActuator
from actors.home_alone import HomeAlone
from actors.power_meter import PowerMeter
from actors.scada import Scada
from actors.simple_sensor import SimpleSensor

switcher = {
    ActorClass.ATN: Atn,
    ActorClass.BOOLEAN_ACTUATOR: BooleanActuator,
    ActorClass.HOME_ALONE: HomeAlone,
    ActorClass.POWER_METER: PowerMeter,
    ActorClass.SCADA: Scada,
    ActorClass.SIMPLE_SENSOR: SimpleSensor,
}


def strategy_from_node(node: ShNode):
    if not node.has_actor:
        return None
    if node.actor_class.value not in [key.value for key in switcher]:
        raise Exception(f"Missing implementation for class {node.actor_class.value}, node {node.alias}!")
    func = switcher[ActorClass(node.actor_class.value)]
    return func


def stickler():
    return None
