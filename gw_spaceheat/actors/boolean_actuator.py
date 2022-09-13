import time
from typing import List, Optional

from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local_maker import (
    GtDispatchBooleanLocal,
    GtDispatchBooleanLocal_Maker,
)
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker import (
    GtDriverBooleanactuatorCmd_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from actors.actor_base import ActorBase
from actors.utils import QOS, Subscription, responsive_sleep


class BooleanActuator(ActorBase):
    MAIN_LOOP_MIN_TIME_S = 5

    def __init__(self, node: ShNode, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super(BooleanActuator, self).__init__(node=node, settings=settings, hardware_layout=hardware_layout)
        self.relay_state: Optional[int] = None
        self.config = NodeConfig(self.node, settings)
        self.screen_print(f"Initialized {self.__class__}")

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [
            Subscription(Topic=f"a.s/{GtDispatchBooleanLocal_Maker.type_alias}", Qos=QOS.AtMostOnce)
        ]
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtDispatchBooleanLocal):
            if from_node is self.scada_node():
                self.gt_dispatch_boolean_local_received(from_node, payload)
            else:
                raise Exception(f"from_node must be {self.scada_node()}")
        else:
            raise Exception(f"{payload} subscription not implemented!")

    def dispatch_relay(self, relay_state: int):
        if relay_state not in [0, 1]:
            raise Exception("expects relay_state of 0 or 1")
        payload = GtDriverBooleanactuatorCmd_Maker(
            relay_state=relay_state,
            command_time_unix_ms=int(time.time() * 1000),
            sh_node_alias=self.node.alias,
        ).tuple
        self.publish(payload)
        if relay_state == 0:
            self.config.driver.turn_off()
        if relay_state == 1:
            self.config.driver.turn_on()

    def gt_dispatch_boolean_local_received(
        self, from_node: ShNode, payload: GtDispatchBooleanLocal
    ):
        if from_node != self.nodes.node("a.s"):
            raise Exception(f"Only responds to dispatch from Scada. Got dispatch from {from_node}")
        if payload.AboutNodeAlias == self.node.alias:
            self.dispatch_relay(payload.RelayState)
            if self.relay_state != payload.RelayState:
                self.update_and_report_state_change()

    def update_and_report_state_change(self):
        new_state = self.config.driver.is_on()
        if self.relay_state != new_state:
            self.screen_print(f"Relay: {self.relay_state} -> {new_state}")
            self.relay_state = new_state
            payload = GtTelemetry_Maker(
                name=self.config.reporting.TelemetryName,
                value=int(self.relay_state),
                exponent=self.config.reporting.Exponent,
                scada_read_time_unix_ms=int(time.time() * 1000),
            ).tuple
            self.publish(payload)

    def sync_report(self):
        payload = GtTelemetry_Maker(
            name=self.config.reporting.TelemetryName,
            value=int(self.relay_state),
            exponent=self.config.reporting.Exponent,
            scada_read_time_unix_ms=int(time.time() * 1000),
        ).tuple
        self.publish(payload)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            check_start_s = time.time()
            self.update_and_report_state_change()
            time_of_read_s = time.time()
            if (time_of_read_s - check_start_s) > self.MAIN_LOOP_MIN_TIME_S:
                return
            wait_time_s = self.MAIN_LOOP_MIN_TIME_S - (time_of_read_s - check_start_s)
            responsive_sleep(self, wait_time_s)

