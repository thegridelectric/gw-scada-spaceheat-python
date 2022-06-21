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
    if node.role not in list(switcher.keys()):
        raise Exception(f"Missing implementation for {node.role.value}!")
    func = switcher[node.role]
    return func


def stickler():
    return None
