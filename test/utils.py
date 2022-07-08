import time
from collections import defaultdict
from typing import Callable, Optional, Dict, Any

import settings
from actors.atn import Atn
from actors.cloud_ear import CloudEar
from actors.scada import Scada
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch import GsDispatch
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import GtDispatchBooleanLocal
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response import GtShCliScadaResponse

LOCAL_MQTT_MESSAGE_DELTA_S = settings.LOCAL_MQTT_MESSAGE_DELTA_S
GW_MQTT_MESSAGE_DELTA = settings.GW_MQTT_MESSAGE_DELTA



def wait_for(
    f: Callable[[], bool],
    timeout: float,
    tag: str = "",
    raise_timeout: bool = True,
    retry_duration: float = 0.1,
) -> bool:
    """Call function f() until it returns True or a timeout is reached. retry_duration specified the sleep time between
    calls. If the timeout is reached before f return True, the function will either raise a ValueError (the default),
    or, if raise_timeout==False, it will return False. Function f is guaranteed to be called at least once. If an
    exception is raised the tag string will be attached to its message.
    """
    now = time.time()
    until = now + timeout
    if now >= until:
        if f():
            return True
    while now < until:
        if f():
            return True
        now = time.time()
        if now < until:
            time.sleep(min(retry_duration, until - now))
            now = time.time()
    if raise_timeout:
        raise ValueError(f"ERROR. Function {f} timed out after {timeout} seconds. {tag}")
    else:
        return False

class AtnRecorder(Atn):
    cli_resp_received: int
    latest_cli_response_payload: Optional[GtShCliScadaResponse]

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.cli_resp_received = 0
        self.latest_cli_response_payload: Optional[GtShCliScadaResponse] = None
        super().__init__(node, logging_on=logging_on)

    def on_gw_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShCliScadaResponse):
            self.cli_resp_received += 1
            self.latest_cli_response_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        return (
            f"AtnRecorder [{self.node.alias}] cli_resp_received: {self.cli_resp_received}  "
            f"latest_cli_response_payload: {self.latest_cli_response_payload}"
        )


class EarRecorder(CloudEar):
    num_received: int
    num_received_by_topic: Dict[str, int]
    latest_payload: Optional[Any]

    def __init__(self, logging_on: bool = False):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.latest_payload = None
        super().__init__(logging_on=logging_on)

    def on_gw_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        s = f"EarRecorder  num_received: {self.num_received}  latest_payload: {self.latest_payload}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n\t{self.num_received_by_topic[topic]:3d}: [{topic}]"
        return s


class ScadaRecorder(Scada):
    """Record data about a PrimaryScada execution during test"""

    num_received: int
    num_received_by_topic: Dict[str, int]

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        super().__init__(node, logging_on=logging_on)

    def on_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_mqtt_message(client, userdata, message)

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        pass

    def gt_dispatch_boolean_local_received(self, payload: GtDispatchBooleanLocal):
        pass

    def summary_str(self):
        """Summarize results in a string"""
        s = f"ScadaRecorder  {self.node.alias}  num_received: {self.num_received}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n\t{self.num_received_by_topic[topic]:3d}: [{topic}]"
        return s
