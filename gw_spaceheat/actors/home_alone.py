import time
from typing import List, Optional

from config import ScadaSettings
from data_classes.sh_node import ShNode
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local_maker import (
    GtDispatchBooleanLocal_Maker,
)
from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus, GtShStatus_Maker

from actors.actor_base import ActorBase
from actors.utils import QOS, Subscription, responsive_sleep


class HomeAlone(ActorBase):
    """HomeAlone is the offline degraded imitator of the AtomicTNode. It dispatches the
    SCADA actor whenever the SCADA's DispatchContract with its AtomicTNode is not alive.
    The primary (but not only) reason for this will be loss of communications (i.e. router
    down or cellular service down) between the home and the cloud."""

    MAIN_LOOP_MIN_TIME_S = 5

    def __init__(self, node: ShNode, settings: ScadaSettings):
        super(HomeAlone, self).__init__(node=node, settings=settings)

        if self.node != self.home_alone_node():
            raise Exception(f"node for HomeAlone must be {self.home_alone_node}, not {self.node}")
        # outrageous stub for tracking the state of the dispatch contract
        self.scada_atn_dispatch_contract_is_alive = False
        self.latest_status: Optional[GtShStatus] = None
        self.screen_print(f"Initialized {self.__class__}")

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [
            Subscription(
                Topic=f"{self.scada_node().alias}/{GtShStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            )
        ]
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        self.screen_print("Got message")
        if isinstance(payload, GtShStatus):
            if from_node is self.scada_node():
                self.gt_sh_status_received(payload)
            else:
                raise Exception(f"Status messages come from {self.scada_node()}")
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gt_sh_status_received(self, payload: GtShStatus):
        """Home alone collects and processes the status information. In combination
        with the time and information about prices and weather it uses the processed
        status data from the last two weeks to make a decision about how to dispatch the
        scada."""

        self.latest_status = payload

    ################################################
    # Primary functions
    ################################################

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            responsive_sleep(self, 300)
            if self.scada_atn_dispatch_contract_is_alive is False:
                dispatch_payload = GtDispatchBooleanLocal_Maker(
                    send_time_unix_ms=int(time.time() * 1000),
                    from_node_alias=self.node.alias,
                    about_node_alias="a.elt1.relay",
                    relay_state=0,
                ).tuple
                self.publish(dispatch_payload)
