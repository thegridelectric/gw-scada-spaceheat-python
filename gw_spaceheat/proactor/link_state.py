import enum
from dataclasses import dataclass
from typing import Optional
from typing import Sequence

from result import Err
from result import Ok
from result import Result

from gwproto import Message

from proactor.message import MQTTConnectFailPayload
from proactor.message import MQTTConnectPayload
from proactor.message import MQTTDisconnectPayload
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload


class StateName(enum.Enum):
    none = "none"
    not_started = "not_started"
        # start()                               ->  start_called         (1)       -> connecting                   *** which start()?

    connecting = "connecting"
        # _process_mqtt_connected               -> mqtt_connected        (2)       -> awaiting_setup_and_peer
        # _process_mqtt_connect_fail            -> mqtt_connect_failed   (3)       -> connecting

    awaiting_setup_and_peer = "awaiting_setup_and_peer"
        # _process_mqtt_suback                  -> mqtt_suback           (4)      -> awaiting_setup_and_peer
        # _process_mqtt_suback                  -> mqtt_suback           (5)      -> awaiting_peer
        # _process_mqtt_message                 -> message_from_peer     (6)      -> awaiting_setup
        # _process_mqtt_disconnected            -> mqtt_disconnected     (7)      -> connecting
        # _process_ack_timeout                  -> response_timeout     (17)      -> awaiting_setup_and_peer

    awaiting_setup = "awaiting_setup"
        # _process_mqtt_suback                  -> mqtt_suback           (8)      -> awaiting_setup
        # _process_mqtt_suback                  -> mqtt_suback           (9)      -> active
        # _process_ack_timeout                  -> response_timeout     (10)      -> awaiting_setup_and_peer
        # _process_mqtt_disconnected            -> mqtt_disconnected    (11)      -> connecting
        # _process_mqtt_message                 -> message_from_peer    (16)      -> awaiting_setup

    awaiting_peer = "awaiting_peer"
        # _process_mqtt_message                 -> message_from_peer    (12)      -> awaiting_setup
        # _process_mqtt_disconnected            -> mqtt_disconnected    (13)      -> connecting
        # _process_ack_timeout                  -> response_timeout     (19)      -> awaiting_peer

    active = "active"
        # _process_ack_timeout                  -> response_timeout     (14)      -> awaiting_peer
        # _process_mqtt_disconnected            -> mqtt_disconnected    (15)      -> connecting

    stopped = "stopped"
        # stop()                               ->  stop_called          (18)      -> stopped                   *** which stop()?

class TransitionName(enum.Enum):
    none = "none"
    start_called = "start_called"
    mqtt_connected = "mqtt_connected"
    mqtt_connect_failed = "mqtt_connect_failed"
    mqtt_disconnected = "mqtt_disconnected"
    mqtt_suback = "mqtt_suback"
    message_from_peer = "message_from_peer"
    response_timeout = "response_timeout"
    stop_called = "stop_called"

@dataclass
class Transition:
    link_name: str = ""
    transition_name: TransitionName = TransitionName.none
    old_state: StateName = StateName.not_started
    new_state: StateName = StateName.not_started

    def __bool__(self) -> bool:
        return self.old_state != self.new_state

    def active(self):
        return self.new_state == StateName.active

    def activated(self):
        return self.old_state != StateName.active and self.new_state == StateName.active

    def deactivated(self):
        return self.old_state == StateName.active and self.new_state != StateName.active

    def set_state(self, state: StateName) -> "Transition":
        self.new_state = state
        return self

@dataclass
class Link:
    name: str = ""
    state: StateName = StateName.not_started

    def active(self):
        return self.state == StateName.active

    def set_state(self, state: StateName, transition_name: TransitionName) -> Transition:
        transition = Transition(self.name, transition_name, self.state)
        self.state = state
        return transition.set_state(self.state)

class InvalidCommStateInput(Exception):
    name: str = ""
    current_state: StateName = StateName.none
    transition: TransitionName = TransitionName.none

    def __init__(
        self,
        name: str = "",
        current_state: StateName = StateName.none,
        transition: TransitionName = TransitionName.none,
        *,
        msg: str = "",
    ):
        self.name = name
        self.current_state = current_state
        self.transition = transition
        super().__init__(msg)

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" [{super_str}]"
        s += f"  for link: [{self.name}]  current state:{self.current_state}  requested transition: {self.transition}"
        return s

class CommLinkMissing(InvalidCommStateInput):
    def __init__(self, name: str, *, msg=""):
        super().__init__(name, msg=msg)

class CommLinkAlreadyExists(InvalidCommStateInput):
    ...


class Links:
    _links: dict[str, Link]

    def __init__(self, names: Optional[Sequence[str]] = None):
        self._links = dict()
        if names is not None:
            for name in names:
                self.add(name)

    def link(self, name) -> Optional[Link]:
        return self._links.get(name, None)

    def link_state(self, name) -> Optional[StateName]:
        if name in self._links:
            return self._links[name].state
        return None

    def __contains__(self, name: str) -> bool:
        return name in self._links

    def __getitem__(self, name: str) -> Link:
        try:
            return self._links[name]
        except KeyError:
            raise CommLinkMissing(name)

    def add(self, name: str, state: StateName = StateName.not_started) -> Link:
        if name in self._links:
            raise CommLinkAlreadyExists(name, current_state=self._links[name].state)
        self._links[name] = Link(name, state)
        return self._links[name]

    def start(self, name:str) -> Result[Transition, InvalidCommStateInput]:
        link = self[name]
        if link.state != StateName.not_started:
            return Err(InvalidCommStateInput(name, current_state=link.state, transition=TransitionName.start_called))
        return Ok(link.set_state(StateName.connecting, TransitionName.start_called))

    def stop(self, name: str) -> Result[Transition, InvalidCommStateInput]:
        return Ok(self[name].set_state(StateName.stopped, TransitionName.stop_called))

    def process_mqtt_connected(self, message: Message[MQTTConnectPayload]) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.mqtt_connected
        link = self[message.Payload.client_name]
        if link.state != StateName.connecting:
            return Err(InvalidCommStateInput(message.Payload.client_name, link.state, transition_name))
        return Ok(link.set_state(StateName.awaiting_setup_and_peer, transition_name))

    def process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.mqtt_disconnected
        link = self[message.Payload.client_name]
        if link.state not in [StateName.awaiting_setup_and_peer, StateName.awaiting_setup, StateName.awaiting_peer, StateName.active]:
            return Err(InvalidCommStateInput(message.Payload.client_name, link.state, transition_name))
        return Ok(link.set_state(StateName.connecting, transition_name))

    def process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.mqtt_connect_failed
        link = self[message.Payload.client_name]
        if link.state != StateName.connecting:
            return Err(InvalidCommStateInput(message.Payload.client_name, link.state, transition_name))
        return Ok(link.set_state(link.state, transition_name))

    def process_mqtt_suback(self, message: Message[MQTTSubackPayload]) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.mqtt_suback
        link = self[message.Payload.client_name]
        if link.state not in [StateName.awaiting_setup_and_peer, StateName.awaiting_setup]:
            return Err(InvalidCommStateInput(message.Payload.client_name, link.state, transition_name))
        new_state = link.state
        if message.Payload.num_pending_subscriptions == 0:
            if link.state == StateName.awaiting_setup_and_peer:
                new_state = StateName.awaiting_peer
            else:
                new_state = StateName.active
        return Ok(link.set_state(new_state, transition_name))

    def process_mqtt_message(self, message: Message[MQTTReceiptPayload]) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.message_from_peer
        link = self[message.Payload.client_name]
        if link.state == StateName.awaiting_setup_and_peer:
            new_state = StateName.awaiting_setup
        elif link.state == StateName.awaiting_peer:
            new_state = StateName.active
        elif link.state == StateName.awaiting_setup:
            new_state = link.state
        else:
            return Err(InvalidCommStateInput(message.Payload.client_name, link.state, transition_name))
        return Ok(link.set_state(new_state, transition_name))

    def process_ack_timeout(self, name: str) -> Result[Transition, InvalidCommStateInput]:
        transition_name = TransitionName.response_timeout
        link = self[name]
        match link.state:
            case StateName.awaiting_setup_and_peer | StateName.awaiting_peer:
                new_state = link.state
            case StateName.awaiting_setup:
                new_state = StateName.awaiting_setup_and_peer
            case StateName.active:
                new_state = StateName.awaiting_peer
            case _:
                return Err(InvalidCommStateInput(name, link.state, transition_name))
        return Ok(link.set_state(new_state, transition_name))



