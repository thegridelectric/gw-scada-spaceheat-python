import time
from typing import Optional, List, Sequence, Dict, Callable

import load_house
from actors.actor_base import ActorBase
from actors.boolean_actuator import BooleanActuator
from actors.power_meter import PowerMeter
from actors.simple_sensor import SimpleSensor
from config import ScadaSettings
from data_classes.sh_node import ShNode

try:
    from test.utils import ScadaRecorder, AtnRecorder, HomeAloneRecorder, wait_for
except ImportError:
    from utils import ScadaRecorder, AtnRecorder, HomeAloneRecorder, wait_for


def delimit_str(text: str = "") -> str:
    return "\n## " + text + ("#" * (100 - len(text)))


def delimit(text: str = ""):
    print(delimit_str(text))


def do_nothing(seconds: float):
    """Let the actors run on their own for a while"""
    if seconds > 0:
        delimit(f"DOING NOTHING FOR {int(seconds):4d} SECONDS")
        time.sleep(seconds)
        delimit("DONE DOING NOTHING")


class Actors:
    scada: ScadaRecorder
    atn: AtnRecorder
    home_alone: HomeAloneRecorder
    relay: BooleanActuator
    meter: PowerMeter
    thermo: SimpleSensor

    def __init__(self, settings: ScadaSettings):
        self.scada = ScadaRecorder(node=ShNode.by_alias["a.s"], settings=settings)
        self.atn = AtnRecorder(node=ShNode.by_alias["a"], settings=settings)
        self.home_alone = HomeAloneRecorder(node=ShNode.by_alias["a.home"], settings=settings)
        self.relay = BooleanActuator(ShNode.by_alias["a.elt1.relay"], settings=settings)
        self.meter = PowerMeter(node=ShNode.by_alias["a.m"], settings=settings)
        self.thermo = SimpleSensor(node=ShNode.by_alias["a.tank.temp0"], settings=settings)


class FragmentRunner:
    settings: ScadaSettings
    actors: Actors
    requested: Dict[str, ActorBase]
    fragments: List["ProtocolFragment"]
    wait_at_least: float
    do_nothing_time: float

    def __init__(
            self,
            settings: ScadaSettings,
            wait_at_least: float = 0.,
            do_nothing_time: float = 0.,
            actors: Optional[Actors] = None
    ):
        self.settings = settings
        self.wait_at_least = wait_at_least
        self.do_nothing_time = do_nothing_time
        self.actors = Actors(settings) if actors is None else actors
        self.requested = dict()
        self.fragments = []

    def add_fragment(self, fragment: "ProtocolFragment") -> "FragmentRunner":
        self.fragments.append(fragment)
        self.wait_at_least = max(self.wait_at_least, fragment.wait_at_least)
        self.request_actors(fragment.get_requested_actors())
        return self

    def request_actors(self, actors: Sequence[ActorBase]) -> "FragmentRunner":
        for actor in actors:
            if actor.node.alias not in self.requested:
                self.requested[actor.node.alias] = actor
        return self

    def start(self):
        for actor in self.requested.values():
            actor.start()

    def wait_connect(self):
        for actor in self.requested.values():
            if hasattr(actor, "client"):
                wait_for(
                    actor.client.is_connected,
                    1,
                    tag=f"ERROR waiting for {actor.node.alias} client connect",
                )
            if hasattr(actor, "gw_client"):
                wait_for(
                    actor.gw_client.is_connected,
                    1,
                    "ERROR waiting for gw_client connect",
                )

    def stop(self):
        for actor in self.requested.values():
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass

    def run(self, *args, **kwargs):
        try:
            start_time = time.time()
            delimit("STARTING")
            self.start()
            self.wait_connect()
            delimit("CONNECTED")
            for fragment in self.fragments:
                fragment.run(*args, **kwargs)
            if (time_left := self.wait_at_least - (time.time() - start_time)) > 0:
                do_nothing(time_left)
        finally:
            self.stop()

    @classmethod
    def run_fragment(cls, fragment_factory: Callable[["FragmentRunner"], "ProtocolFragment"]):
        settings = ScadaSettings(log_message_summary=True)
        load_house.load_all(settings.world_root_alias)
        runner = FragmentRunner(settings)
        runner.add_fragment(fragment_factory(runner))
        runner.run()


class ProtocolFragment:
    runner: FragmentRunner
    wait_at_least: float

    def __init__(self, runner: FragmentRunner, wait_at_least: float = 0):
        self.runner = runner
        self.wait_at_least = wait_at_least

    def get_requested_actors(self) -> Sequence[ActorBase]:
        pass

    def run(self, *args, **kwargs):
        pass
