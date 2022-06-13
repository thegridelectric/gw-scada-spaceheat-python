import csv
import threading
import time
from typing import Dict, List

import pendulum
from actors.primary_scada.primary_scada_base import PrimaryScadaBase
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import \
    GridworksSimBool30AmpRelay_BooleanActuatorDriver
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import \
    NcdPr814Spst_BooleanActuatorDriver
from schema.enums.make_model.make_model_map import MakeModel
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry


class PrimaryScada(PrimaryScadaBase):

    def __init__(self, node: ShNode):
        super(PrimaryScada, self).__init__(node=node)
        self.power = 0
        self.total_power_w = 0
        self.driver: Dict[ShNode, BooleanActuatorDriver] = {}
        self.temp_readings: List = []
        self.set_actuator_components()
        self.consume()
        self.gw_consume()
        self.schedule_thread = threading.Thread(target=self.main)
        self.schedule_thread.start()
        self.screen_print(f'Started {self.__class__}')

    def set_actuator_components(self):
        self.boost_actuator = ShNode.by_alias['a.elt1.relay']
        if self.boost_actuator.primary_component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.boost_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.boost_actuator.primary_component)
        elif self.boost_actuator.primary_component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.boost_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.boost_actuator.primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {self.boost_actuator.primary_component.make_model}")

        self.pump_actuator = ShNode.by_alias['a.tank.out.pump.relay']

        if self.pump_actuator.primary_component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.pump_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.pump_actuator.primary_component)
        elif self.pump_actuator.primary_component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.pump_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.pump_actuator.primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {self.pump_actuator.primary_component.make_model}")

    def gs_pwr_received(self, payload: GsPwr, from_node: ShNode):
        if from_node != ShNode.by_alias['a.m']:
            raise Exception("Need to track all metering and make sure we have the sum")
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.gw_publish(payload=payload)
    
    def gt_telemetry_received(self, payload: GtTelemetry, from_node: ShNode):
        self.screen_print(f"{payload.Value} from {from_node.alias}")
        t_unix_s = int(payload.ScadaReadTimeUnixMs / 1000)
        t = pendulum.from_timestamp(t_unix_s)
        ms = payload.ScadaReadTimeUnixMs % 1000
        self.temp_readings.append([t.strftime("%Y-%m-%d %H:%M:%S"), t_unix_s, ms, from_node.alias, payload.Value])

    def gs_dispatch_received(self, payload: GsDispatch, from_node: ShNode):
        raise NotImplementedError
    
    def turn_on(self, ba: ShNode):
        if not isinstance(ba.primary_component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_on()

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.primary_component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_off()

    def terminate_scheduling(self):
        self._scheduler_running = False

    def main(self):
        self._scheduler_running = True
        while self._scheduler_running is True:
            # track time and send status every x minutes (likely 5)
            time.sleep(1)
