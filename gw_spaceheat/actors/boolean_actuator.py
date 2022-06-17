import time
from typing import List

from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode

from schema.gs.gs_dispatch_maker import GsDispatch, GsDispatch_Maker
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from actors.actor_base import ActorBase
from actors.utils import QOS, Subscription


class BooleanActuator(ActorBase):
    MAIN_LOOP_MIN_TIME_S = 5

    def __init__(self, node: ShNode):
        super(BooleanActuator, self).__init__(node=node)
        now = int(time.time())
        self._last_sync_report_time_s = (now - (now % 300) - 60)
        self.relay_state: int = None
        self.config = NodeConfig(self.node)
        self.screen_print(f"Initialized {self.__class__}")

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [Subscription(Topic=f'a.s/{GsDispatch_Maker.type_alias}', Qos=QOS.AtMostOnce)]
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
        if isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception(f"Only responds to dispatch from Scada. Got dispatch from {from_node}")
        old_state = self.relay_state
        new_state = payload.RelayState
        if payload.RelayState == 0:
            self.config.driver.turn_off()
        elif payload.RelayState == 1:
            self.config.driver.turn_on()
        if old_state != new_state:
            self.update_and_report_state_change()

    def update_and_report_state_change(self):
        new_state = self.config.driver.is_on()
        if self.relay_state != new_state:
            self.relay_state = new_state
            payload = GtTelemetry_Maker(name=self.config.reporting.TelemetryName,
                                        value=int(self.relay_state),
                                        exponent=self.config.reporting.Exponent,
                                        scada_read_time_unix_ms=int(time.time() * 1000)).tuple
            self.publish(payload)

    def sync_report(self):
        payload = GtTelemetry_Maker(name=self.config.reporting.TelemetryName,
                                    value=int(self.relay_state),
                                    exponent=self.config.reporting.Exponent,
                                    scada_read_time_unix_ms=int(time.time() * 1000)).tuple
        self.publish(payload)
        self._last_sync_report_time_s = time.time()

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            check_start_s = time.time()
            self.update_and_report_state_change()
            if self.time_for_sync_report():
                self.sync_report()

            time_of_read_s = time.time()
            if (time_of_read_s - check_start_s) > self.MAIN_LOOP_MIN_TIME_S:
                return
            wait_time_s = self.MAIN_LOOP_MIN_TIME_S - (time_of_read_s - check_start_s)
            time.sleep(wait_time_s)

    @property
    def next_sync_report_time_s(self) -> int:
        next_s = self._last_sync_report_time_s + 300
        return next_s - (next_s % 300) + 240

    def time_for_sync_report(self) -> bool:
        if time.time() > self.next_sync_report_time_s:
            return True
        return False
