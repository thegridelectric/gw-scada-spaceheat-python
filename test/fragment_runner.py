import asyncio
import time
from typing import Optional, List, Sequence, Dict, Callable

import actors2
import load_house
from actors.actor_base import ActorBase
from actors.boolean_actuator import BooleanActuator
from actors.power_meter import PowerMeter
from actors.simple_sensor import SimpleSensor
from actors2 import Scada2, ActorInterface
from config import ScadaSettings
from data_classes.sh_node import ShNode

try:
    from test.utils import (
        ScadaRecorder,
        AtnRecorder,
        HomeAloneRecorder,
        wait_for,
        await_for,
    )
except ImportError:
    from utils import ScadaRecorder, AtnRecorder, HomeAloneRecorder, wait_for, await_for


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


async def async_do_nothing(seconds: float):
    if seconds > 0:
        delimit(f"DOING NOTHING FOR {int(seconds):4d} SECONDS")
        await asyncio.sleep(seconds)
        delimit("DONE DOING NOTHING")


class Actors:
    scada: ScadaRecorder
    atn: AtnRecorder
    home_alone: HomeAloneRecorder
    relay: BooleanActuator
    meter: PowerMeter
    thermo: SimpleSensor
    scada2: Scada2
    relay2: actors2.BooleanActuator

    def __init__(self, settings: ScadaSettings):
        self.scada = ScadaRecorder(node=ShNode.by_alias["a.s"], settings=settings)
        self.atn = AtnRecorder(node=ShNode.by_alias["a"], settings=settings)
        self.home_alone = HomeAloneRecorder(
            node=ShNode.by_alias["a.home"], settings=settings
        )
        self.relay = BooleanActuator(ShNode.by_alias["a.elt1.relay"], settings=settings)
        self.meter = PowerMeter(node=ShNode.by_alias["a.m"], settings=settings)
        self.thermo = SimpleSensor(
            node=ShNode.by_alias["a.tank.temp0"], settings=settings
        )
        self.scada2 = Scada2(ShNode.by_alias["a.s"], settings, actors=dict())
        self.relay2 = actors2.BooleanActuator(
            node=ShNode.by_alias["a.elt1.relay"], services=self.scada2
        )


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
        wait_at_least: float = 0.0,
        do_nothing_time: float = 0.0,
        actors: Optional[Actors] = None,
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
        self.request_actors2(fragment.get_requested_actors2())
        return self

    def request_actors(self, actors: Sequence[ActorBase]) -> "FragmentRunner":
        for actor in actors:
            if actor.node.alias not in self.requested:
                self.requested[actor.node.alias] = actor
        return self

    def request_actors2(self, actors: Sequence[ActorInterface]) -> "FragmentRunner":
        # TODO: There should be some test-public interface for this
        for actor in actors:
            # noinspection PyProtectedMember
            self.actors.scada2._add_communicator(actor)
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

    async def await_connect(self):
        for actor in self.requested.values():
            if hasattr(actor, "client"):
                await await_for(
                    actor.client.is_connected,
                    1,
                    tag=f"ERROR waiting for {actor.node.alias} client connect",
                )
            if hasattr(actor, "gw_client"):
                await await_for(
                    actor.gw_client.is_connected,
                    1,
                    "ERROR waiting for gw_client connect",
                )
            # TODO: make some test-public form of this
            if hasattr(actor, "_mqtt_clients"):
                # noinspection PyProtectedMember
                for client_name in actor._mqtt_clients._clients:
                    # noinspection PyProtectedMember
                    await await_for(
                        lambda: actor._mqtt_clients.subscribed(client_name),
                        3,
                        f"waiting for {client_name} connect",
                    )

    def stop(self):
        for actor in self.requested.values():
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass

    async def stop_and_join(self):
        for actor in self.requested.values():
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass
        for actor in self.requested.values():
            if hasattr(actor, "join"):
                # noinspection PyBroadException
                try:
                    await actor.join()
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

    async def async_run(self, *args, **kwargs):
        try:
            start_time = time.time()
            delimit("STARTING")
            self.start()
            # TODO: Work out how this fits with Scada2.start()
            asyncio.create_task(self.actors.scada2.run_forever(), name="run_forever")
            await self.await_connect()
            delimit("CONNECTED")
            for fragment in self.fragments:
                await fragment.async_run(*args, **kwargs)
            if (time_left := self.wait_at_least - (time.time() - start_time)) > 0:
                await async_do_nothing(time_left)
        finally:
            # noinspection PyBroadException
            try:
                await self.stop_and_join()
            except:
                pass

            # TODO: What the heck? We should understand this.
            #       This obscures scary-but-harmless-(???) "Task was destroyed but it is pending!" errors
            #       apparently due to cancelling tasks without the loop being able to clean them up.
            #       What is the right way of dealing with this?
            await asyncio.sleep(0.1)

    @classmethod
    def run_fragment(
        cls, fragment_factory: Callable[["FragmentRunner"], "ProtocolFragment"]
    ):
        settings = ScadaSettings(log_message_summary=True)
        load_house.load_all(settings.world_root_alias)
        runner = FragmentRunner(settings)
        runner.add_fragment(fragment_factory(runner))
        runner.run()

    @classmethod
    async def async_run_fragment(
        cls, fragment_factory: Callable[["FragmentRunner"], "ProtocolFragment"]
    ):
        settings = ScadaSettings(log_message_summary=True)
        load_house.load_all(settings.world_root_alias)
        runner = FragmentRunner(settings)
        runner.add_fragment(fragment_factory(runner))
        await runner.async_run()


class ProtocolFragment:
    runner: FragmentRunner
    wait_at_least: float

    def __init__(self, runner: FragmentRunner, wait_at_least: float = 0):
        self.runner = runner
        self.wait_at_least = wait_at_least

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return []

    # noinspection PyMethodMayBeStatic
    def get_requested_actors2(self) -> Sequence[ActorInterface]:
        return []

    def run(self, *args, **kwargs):
        pass

    async def async_run(self, *args, **kwargs):
        pass
