import time
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName

from actors.actor_base import ActorBase
from data_classes.errors import DataClassLoadingError
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import NcdPr814Spst_BooleanActuatorDriver
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import \
    GridworksSimBool30AmpRelay_BooleanActuatorDriver

from schema.enums.make_model.make_model_map import MakeModel
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker


class BooleanActuator(ActorBase):
    def __init__(self, node: ShNode):
        super(BooleanActuator, self).__init__(node=node)
        now = int(time.time())
        self._last_sync_report_time_s = (now - (now % 300) - 60)
        self.relay_state: int = None
        self.driver: BooleanActuatorDriver = None
        self.cac: BooleanActuatorCac = self.component.cac
        self.set_driver()
        self.screen_print(f"Initialized {self.__class__}")

    def set_driver(self):
        if self.component.cac.make_model == MakeModel.NCD__PR814SPST:
            self.driver = NcdPr814Spst_BooleanActuatorDriver(component=self.component)
        else:
            self.driver = GridworksSimBool30AmpRelay_BooleanActuatorDriver(component=self.component)

    def main(self):
        while True:
            new_state = self.driver.is_on()
            if self.relay_state != new_state:
                self.relay_state = int(new_state)
                payload = GtTelemetry_Maker(name=TelemetryName.RELAY_STATE,
                                            value=int(self.relay_state),
                                            scada_read_time_unix_ms=int(time.time() * 1000)).tuple
                self.publish(payload)
            if self.time_for_sync_report():
                payload = GtTelemetry_Maker(name=TelemetryName.RELAY_STATE,
                                            value=int(self.relay_state),
                                            scada_read_time_unix_ms=int(time.time() * 1000)).tuple
                self.publish(payload)
                self._last_sync_report_time = time.time()
            time.sleep(1)

    @property
    def component(self) -> BooleanActuatorComponent:
        if self.node.component_id is None:
            return None
        if self.node.component_id not in BooleanActuatorComponent.by_id.keys():
            raise DataClassLoadingError(f"{self.node.alias} component {self.node.component_id} \
                not in BooleanActuatorComponents!")
        return BooleanActuatorComponent.by_id[self.node.component_id]

    @property
    def next_sync_report_time_s(self) -> int:
        next_s = self._last_sync_report_time_s + 300
        return next_s - (next_s % 300) + 240

    def time_for_sync_report(self) -> bool:
        if time.time() > self.next_sync_report_time_s:
            return True
        return False
