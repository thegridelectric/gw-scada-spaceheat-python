import argparse
import asyncio
import logging
import time
import uuid
from typing import Callable
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

import actors
from actors import ActorInterface
from actors.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from logging_setup import setup_logging
from tests.atn import Atn
from gwproactor import Proactor
from tests.atn import AtnSettings

try:
    from tests.utils.scada_recorder import ScadaRecorder
    from tests.utils.wait import await_for
    from tests.utils.wait import wait_for
except ImportError:
    from .scada_recorder import ScadaRecorder
    from .wait import await_for
    from .wait import wait_for


def delimit_str(text: str = "") -> str:
    return "\n## " + text + ("#" * (150 - len(text)))


def delimit(text: str = "", logger: Optional[logging.Logger] = None):
    s = delimit_str(text)
    if logger is None:
        print(s)
    else:
        logger.log(logging.ERROR - 1, s.lstrip())

def do_nothing(seconds: float, logger: Optional[logging.Logger] = None):
    """Let the actors run on their own for a while"""
    if seconds > 0:
        delimit(f"DOING NOTHING FOR {int(seconds):4d} SECONDS", logger)
        time.sleep(seconds)
        delimit("DONE DOING NOTHING", logger)


async def async_do_nothing(seconds: float, logger: Optional[logging.Logger] = None):
    if seconds > 0:
        delimit(f"DOING NOTHING FOR {int(seconds):4d} SECONDS", logger)
        await asyncio.sleep(seconds)
        delimit("DONE DOING NOTHING", logger)


class Actors:
    atn: Atn
    scada: ScadaRecorder
    relay: actors.BooleanActuator
    meter: actors.PowerMeter

    def __init__(
            self,
            settings: ScadaSettings,
            layout: HardwareLayout,
            **kwargs
    ):
        settings.paths.mkdirs(parents=True)
        atn_settings = kwargs.get("atn_settings", AtnSettings())
        atn_settings.paths.mkdirs(parents=True)
        self.atn = kwargs.get(
            "atn",
            Atn("a", settings=atn_settings, hardware_layout=layout)
        )
        self.scada = kwargs.get(
            "scada",
            ScadaRecorder("a.s", settings, hardware_layout=layout)
        )
        self.relay = kwargs.get(
            "relay",
            actors.BooleanActuator("a.elt1.relay", services=self.scada)
        )
        self.thermo = kwargs.get(
            "thermo",
            actors.SimpleSensor("a.tank.temp0", services=self.scada)
        )
        self.meter = kwargs.get(
            "meter",
            actors.PowerMeter("a.m", services=self.scada)
        )


class ProtocolFragment:
    runner: "AsyncFragmentRunner"
    wait_at_least: float

    def __init__(self, runner: "AsyncFragmentRunner", wait_at_least: float = 0):
        self.runner = runner
        self.wait_at_least = wait_at_least

    def get_requested_proactors(self) -> Sequence[Proactor]:
        return []

    def get_requested_actors(self) -> Sequence[ActorInterface]:
        return []

    async def async_run(self, *args, **kwargs):
        pass

class AsyncFragmentRunner:

    settings: ScadaSettings
    atn_settings: AtnSettings
    layout: HardwareLayout
    actors: Actors
    proactors: Dict[str, Proactor]
    fragments: List[ProtocolFragment]
    wait_at_least: float
    do_nothing_time: float
    tag: str
    logger: logging.Logger
    uid: str

    def __init__(
        self,
        settings: ScadaSettings,
        atn_settings: AtnSettings,
        wait_at_least: float = 0.0,
        do_nothing_time: float = 0.0,
        actors: Optional[Actors] = None,
        tag: str = "",
        args: Optional[argparse.Namespace] = None,
    ):
        if settings is None:
            settings = ScadaSettings()
        if atn_settings is None:
            atn_settings = AtnSettings()
        settings.paths.mkdirs(parents=True)
        atn_settings.paths.mkdirs(parents=True)
        errors = []
        if args is None:
            args = argparse.Namespace(verbose=True)
        setup_logging(args, settings, errors, add_screen_handler=True)
        assert not errors
        setup_logging(args, cast(ScadaSettings, atn_settings), errors, add_screen_handler=False)
        assert not errors

        self.settings = settings
        self.logger = logging.getLogger(self.settings.logging.base_log_name)
        self.atn_settings = atn_settings
        self.tag = tag
        self.uid = str(uuid.uuid4())
        self.layout = HardwareLayout.load(settings.paths.hardware_layout)
        self.wait_at_least = wait_at_least
        self.do_nothing_time = do_nothing_time
        self.actors = Actors(
            settings,
            self.layout,
            atn_settings=atn_settings,
        ) if actors is None else actors
        self.proactors = dict()
        self.fragments = []

    def delimit(self, text: str = "") -> None:
        if self.logger:
            self.logger.log(logging.ERROR - 1, "\n")
        else:
            print()
        delimit(text + " ", self.logger)
        delimit(f"{text}  [{self.tag}]  [{self.uid}] ", self.logger)
        delimit(text + " ", self.logger)


    def add_fragment(self, fragment: "ProtocolFragment") -> "AsyncFragmentRunner":
        self.fragments.append(fragment)
        self.wait_at_least = max(self.wait_at_least, fragment.wait_at_least)
        self.request_proactors(fragment.get_requested_proactors())
        self.request_actors(fragment.get_requested_actors())
        return self

    def request_proactors(self, proactors: Sequence[Proactor]) -> "AsyncFragmentRunner":
        for proactor in proactors:
            if proactor.name not in self.proactors:
                self.proactors[proactor.name] = proactor
        return self

    def request_actors(self, actors: Sequence[ActorInterface]) -> "AsyncFragmentRunner":
        for actor in actors:
            self.actors.scada.add_communicator(actor)
        return self

    async def await_connect(self, logger: Optional[logging.Logger] = None):
        for proactor in self.proactors.values():
            # noinspection PyProtectedMember, PyShadowingNames
            connected = await await_for(
                lambda: all([proactor._mqtt_clients.subscribed(client_name)
                            for client_name in proactor._mqtt_clients.clients.keys()]),
                10,
                raise_timeout=False
            )
            if not connected:
                s = "MQTT CONNECTION ERROR\n"
                # noinspection PyProtectedMember, PyShadowingNames
                for client_name in sorted(proactor._mqtt_clients.clients.keys()):
                    # noinspection PyProtectedMember
                    client = proactor._mqtt_clients.clients[client_name]
                    # noinspection PyProtectedMember
                    s += (
                        f"  {client_name:20s}  subscribed:{int(client.subscribed())}"
                        f"  connected:{int(client.connected())} ({client._client_config.host}:{client._client_config.port})"
                        f"  subs:{client.num_subscriptions()}   subs pending: {client.num_pending_subscriptions()}\n"
                    )
                if logger is not None:
                    logger.info(s)
                raise ValueError(s)

    async def stop_and_join(self):
        for proactor in self.proactors.values():
            # noinspection PyBroadException
            try:
                proactor.stop()
            except:
                pass
        for proactor in self.proactors.values():
            if hasattr(proactor, "join"):
                # noinspection PyBroadException
                try:
                    await proactor.join()
                except:
                    pass

    async def async_run(self, *args, **kwargs):
        try:
            start_time = time.time()
            self.delimit("STARTING")
            # TODO: Make this public access
            # noinspection PyProtectedMember
            self.actors.scada._mqtt_clients.enable_loggers(self.actors.scada._logger)
            if self.actors.atn.name in self.proactors:
                asyncio.create_task(self.actors.atn.run_forever(), name="atn_run_forever")
            asyncio.create_task(self.actors.scada.run_forever(), name="scada_run_forever")
            # TODO: Make _logger public
            # noinspection PyProtectedMember
            await self.await_connect(cast(logging.Logger, self.actors.scada._logger))
            # noinspection PyProtectedMember
            self.actors.scada._mqtt_clients.disable_loggers()
            self.delimit("CONNECTED")
            for fragment in self.fragments:
                await fragment.async_run(*args, **kwargs)
            if (time_left := self.wait_at_least - (time.time() - start_time)) > 0:
                await async_do_nothing(time_left, self.logger)
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
            # noinspection PyBroadException
            try:
                self.delimit("COMPLETE")
            except:
                pass

    @classmethod
    async def async_run_fragment(
        cls,
        fragment_factory: Callable[["AsyncFragmentRunner"], ProtocolFragment],
        settings: Optional[ScadaSettings] = None,
        atn_settings: Optional[AtnSettings] = None,
        args: Optional[argparse.Namespace] = None,
        tag: str = ""
    ):
        runner = AsyncFragmentRunner(settings, atn_settings=atn_settings, tag=tag, args=args)
        runner.add_fragment(fragment_factory(runner))
        await runner.async_run()


