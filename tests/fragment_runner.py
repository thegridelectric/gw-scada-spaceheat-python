import asyncio
import logging
import time
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

import actors2
from actors2 import ActorInterface
from actors.actor_base import ActorBase
from actors.boolean_actuator import BooleanActuator
from actors.power_meter import PowerMeter
from actors.simple_sensor import SimpleSensor
from config import LoggingSettings
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from tests.atn import Atn2
from proactor import Proactor
from tests.atn import AtnSettings
from tests.utils import AtnRecorder

try:
    from tests.utils import HomeAloneRecorder
    from tests.utils import Scada2Recorder
    from tests.utils import ScadaRecorder
    from tests.utils import await_for
    from tests.utils import wait_for
except ImportError:
    from utils import HomeAloneRecorder
    from utils import Scada2Recorder
    from utils import ScadaRecorder
    from utils import await_for
    from utils import wait_for


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
    atn2: Atn2
    scada2: Scada2Recorder
    relay2: actors2.BooleanActuator
    meter2: actors2.PowerMeter

    def __init__(
            self,
            settings: ScadaSettings,
            layout: HardwareLayout,
            **kwargs
    ):
        self.scada = kwargs.get(
            "scada",
            ScadaRecorder("a.s", settings=settings, hardware_layout=layout)
        )
        self.atn = kwargs.get(
            "atn",
            AtnRecorder("a", settings=settings, hardware_layout=layout)
        )
        self.home_alone = kwargs.get(
            "home_alone",
            HomeAloneRecorder("a.home", settings=settings, hardware_layout=layout)
        )
        self.relay = kwargs.get(
            "relay",
            BooleanActuator("a.elt1.relay", settings=settings, hardware_layout=layout)
        )
        self.meter = kwargs.get(
            "power_meter",
            PowerMeter("a.m", settings=settings, hardware_layout=layout)
        )
        self.thermo = kwargs.get(
            "thermo",
            SimpleSensor("a.tank.temp0", settings=settings, hardware_layout=layout)
        )
        self.atn2 = kwargs.get(
            "atn",
            Atn2("a", settings=kwargs.get("atn_settings", AtnSettings()), hardware_layout=layout)
        )
        self.scada2 = kwargs.get(
            "scada2",
            Scada2Recorder("a.s", settings, hardware_layout=layout)
        )
        self.relay2 = kwargs.get(
            "relay2",
            actors2.BooleanActuator("a.elt1.relay", services=self.scada2)
        )
        self.thermo2 = kwargs.get(
            "thermo2",
            actors2.SimpleSensor("a.tank.temp0", services=self.scada2)
        )
        self.meter2 = kwargs.get(
            "meter2",
            actors2.PowerMeter("a.m", services=self.scada2)
        )

class ProtocolFragment:
    runner: "FragmentRunner"
    wait_at_least: float

    def __init__(self, runner: "FragmentRunner", wait_at_least: float = 0):
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


class FragmentRunner:
    settings: ScadaSettings
    layout: HardwareLayout
    actors: Actors
    requested: Dict[str, ActorBase]
    fragments: List[ProtocolFragment]
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
        self.layout = HardwareLayout.load(settings.paths.hardware_layout)
        self.wait_at_least = wait_at_least
        self.do_nothing_time = do_nothing_time
        self.actors = Actors(settings, self.layout) if actors is None else actors
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
            # TODO: make some test-public form of this
            if hasattr(actor, "_mqtt_clients"):
                # noinspection PyProtectedMember
                for client_name in actor._mqtt_clients._clients:
                    # noinspection PyProtectedMember
                    wait_for(
                        lambda: actor._mqtt_clients.subscribed(client_name),
                        3,
                        f"waiting for {client_name} connect",
                    )

    def stop(self):
        for actor in self.requested.values():
            # noinspection PyBroadException
            try:
                if isinstance(actor, Atn2):
                    actor.stop_and_join_thread()
                else:
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

    @classmethod
    def run_fragment(
        cls, fragment_factory: Callable[["FragmentRunner"], ProtocolFragment]
    ):
        settings = ScadaSettings(logging=LoggingSettings(base_log_level=logging.DEBUG))
        settings.paths.mkdirs(parents=True)
        runner = FragmentRunner(settings)
        runner.add_fragment(fragment_factory(runner))
        runner.run()


class AsyncFragmentRunner(FragmentRunner):

    def add_fragment(self, fragment: "ProtocolFragment") -> "AsyncFragmentRunner":
        self.fragments.append(fragment)
        self.wait_at_least = max(self.wait_at_least, fragment.wait_at_least)
        self.request_actors(fragment.get_requested_actors())
        self.request_actors2(fragment.get_requested_actors2())
        return self

    def request_actors2(self, actors: Sequence[ActorInterface]) -> "AsyncFragmentRunner":
        for actor in actors:
            # noinspection PyProtectedMember
            self.actors.scada2.add_communicator(actor)
        return self

    def start(self):
        for actor in self.requested.values():
            if not isinstance(actor, Proactor):
                actor.start()

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

    async def async_run(self, *args, **kwargs):
        try:
            start_time = time.time()
            delimit("STARTING")
            self.start()
            if self.actors.atn2.name in self.requested:
                asyncio.create_task(self.actors.atn2.run_forever(), name="atn_run_forever")
            asyncio.create_task(self.actors.scada2.run_forever(), name="scada_run_forever")
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
    async def async_run_fragment(
        cls,
        fragment_factory: Callable[["AsyncFragmentRunner"], ProtocolFragment],
        settings: Optional[ScadaSettings] = None
    ):
        if settings is None:
            settings = ScadaSettings()
        runner = AsyncFragmentRunner(settings)
        runner.add_fragment(fragment_factory(runner))
        await runner.async_run()


