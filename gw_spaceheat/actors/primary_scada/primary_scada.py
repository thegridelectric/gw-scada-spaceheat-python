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
        self.calibrate_thread.start()
        self.consume_thread.start()
        self.screen_print(f"Started PrimaryScada {self.node}")

    def calibrate(self):
        while True:
            time.sleep(60)
            self.screen_print("appending output")
            with open(self.CALIBRATION_FILE, 'a') as outfile:
                write = csv.writer(outfile, delimiter=',')
                for row in self.temp_readings:
                    write.writerow(row)
            self.temp_readings = []

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
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.publish_gs_pwr(payload=payload)
    
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