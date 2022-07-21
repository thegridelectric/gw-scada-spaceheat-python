"""Sample driver script showing message in/out summary lines for a portion of the mqtt protocol."""
import enum
import sys
import argparse
import time
import typing
from typing import Optional, List, Sequence, Dict

import dotenv

import load_house
from actors.actor_base import ActorBase
from actors.atn import Atn
from actors.boolean_actuator import BooleanActuator
from actors.cloud_ear import CloudEar
from actors.power_meter import PowerMeter
from actors.simple_sensor import SimpleSensor
from command_line_utils import add_default_args, setup_logging
from config import ScadaSettings
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import GridworksSimPm1_PowerMeterDriver
from utils import ScadaRecorder, AtnRecorder, HomeAloneRecorder, wait_for

# noinspection PyUnusedLocal


def i_am_quiet(self, note: str):
    """Replaces screen_print with silence"""
    pass


def please_be_quiet():
    """Monkey patch screen_print() to do nothing."""
    ActorBase.screen_print = i_am_quiet
    Atn.screen_print = i_am_quiet
    CloudEar.screen_print = i_am_quiet


class FragmentNames(enum.Enum):
    all = "all"
    meter = "meter"
    GsPwr = "GsPwr"
    thermo = "thermo"


def add_show_protocol_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add show_protocol only args"""
    parser.add_argument("--do-nothing-time", default=0, help="Length of delays between steps, if any.", type=float)
    parser.add_argument(
        "-f", "--fragments",
        default=[],
        help="Names of fragments to run.",
        choices=[entry.value for entry in FragmentNames],
        nargs="+",
    )
    parser.add_argument("-w", "--wait-at-least", default=0, help="Time to wait for all periodic fragments", type=float)
    return parser


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
    args: argparse.Namespace
    settings: ScadaSettings
    actors: Actors
    requested: Dict[str, ActorBase]
    fragments: List["ProtocolFragment"]
    wait_at_least: float

    def __init__(self, args: argparse.Namespace, settings: ScadaSettings, actors: Actors):
        self.args = args
        self.settings = settings
        self.actors = actors
        self.requested = dict()
        self.fragments = []
        self.wait_at_least = args.wait_at_least
        if not self.args.fragments:
            self.args.fragments = ["all"]
        for fragment in [self.fragment_from_enum(FragmentNames(name)) for name in self.args.fragments]:
            self.fragments.append(fragment)
            self.wait_at_least = max(self.wait_at_least, fragment.wait_at_least)
            self.request(fragment.get_requested_actors(self.actors))

    def fragment_from_enum(self, name: FragmentNames) -> "ProtocolFragment":
        if name == FragmentNames.all:
            fragment = AllFragments(self)
        elif name == FragmentNames.thermo:
            fragment = ThermoFragment(self)
        elif name == FragmentNames.meter:
            fragment = MeterFragment(self)
        elif name == FragmentNames.GsPwr:
            fragment = GsPwrFragment(self)
        else:
            raise ValueError(f"Unknown fragment name {name}")
        return fragment

    def request(self, actors: Sequence[ActorBase]):
        for actor in actors:
            if actor.node.alias not in self.requested:
                self.requested[actor.node.alias] = actor

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

    def run(self):
        try:
            start_time = time.time()
            delimit("STARTING")
            self.start()
            self.wait_connect()
            delimit("CONNECTED")
            for fragment in self.fragments:
                fragment.run(self.actors)
            if (time_left := self.wait_at_least - (time.time() - start_time)) > 0:
                do_nothing(time_left)
        finally:
            self.stop()


class ProtocolFragment:
    args: argparse.Namespace
    settings: ScadaSettings
    wait_at_least: float

    def __init__(self, runner: FragmentRunner, wait_at_least: float = 0):
        self.args = runner.args
        self.settigns = runner.settings
        self.wait_at_least = wait_at_least

    def get_requested_actors(self, actors: Actors) -> Sequence[ActorBase]:
        pass

    def run(self, actors: Actors):
        pass


class WaitingFragment(ProtocolFragment):

    def __init__(self, runner: FragmentRunner):
        super().__init__(runner, wait_at_least=runner.args.wait_at_least)


class ThermoFragment(WaitingFragment):

    def get_requested_actors(self, actors: Actors) -> Sequence[ActorBase]:
        return [actors.scada, actors.thermo]


class MeterFragment(WaitingFragment):

    def get_requested_actors(self, actors: Actors) -> Sequence[ActorBase]:
        return [actors.scada, actors.meter]


class GsPwrFragment(ProtocolFragment):

    def get_requested_actors(self, actors: Actors) -> Sequence[ActorBase]:
        return [actors.scada, actors.meter, actors.atn]

    def run(self, actors: Actors):
        actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
        num_sets = 10
        for i in range(num_sets):
            print(f"Setting GsPwr {i+1:2d}/{num_sets}")
            typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                actors.meter.driver
            ).fake_power_w += 1000
            time.sleep(1)
        time.sleep(5)


class AllFragments(ProtocolFragment):

    def get_requested_actors(self, actors: Actors) -> Sequence[ActorBase]:
        return [
            actors.scada,
            actors.atn,
            actors.home_alone,
            actors.relay,
            actors.meter,
            actors.thermo
        ]

    def run(self, actors: Actors):
        actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True

        do_nothing(self.args.do_nothing_time)

        delimit("TURNING ON")
        actors.atn.turn_on(ShNode.by_alias["a.elt1.relay"])
        wait_for(lambda: actors.relay.relay_state == 1, 10, f"Relay state")
        delimit("TURNED ON")

        do_nothing(self.args.do_nothing_time)

        delimit("REQUESTING STATUS")
        actors.atn.status()
        wait_for(
            lambda: actors.atn.cli_resp_received > 0, 10, f"cli_resp_received == 0 {actors.atn.summary_str()}"
        )

        wait_for(
            lambda: actors.scada.num_received_by_topic["a.elt1.relay/gt.telemetry.110"] > 0,
            10,
            f"scada elt telemetry. {actors.scada.summary_str()}",
        )

        # wait_for(lambda: scada.num_received_by_topic["a.m/p"] > 0, 10, f"scada power. {scada.summary_str()}")
        # This should report after turning on the relay. But that'll take a simulated element
        # that actually turns on and can be read by the simulated power meter

        wait_for(
            lambda: actors.scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] > 0,
            10,
            f"scada temperature. {actors.scada.summary_str()}",
        )
        delimit("SCADA GOT STATUS")

        do_nothing(self.args.do_nothing_time)

        delimit("SCADA SENDING STATUS")
        actors.scada.send_status()
        wait_for(lambda: actors.atn.status_received > 0, 10, f"atn summary. {actors.atn.summary_str()}")
        wait_for(
            lambda: actors.home_alone.status_received > 0,
            10,
            f"home alone summary. {actors.home_alone.summary_str()}",
        )
        delimit("SCADA STATUS RECEIVED")


def show_protocol(argv: Optional[List[str]] = None):
    """Run protocol fragments, showing their result on screen"""
    args = add_show_protocol_args(
        add_default_args(
            argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        )
    ).parse_args(sys.argv[1:] if argv is None else argv)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file), log_message_summary=True)
    setup_logging(args, settings)
    please_be_quiet()
    load_house.load_all(settings.world_root_alias)
    runner = FragmentRunner(args, settings, Actors(settings))
    runner.run()

if __name__ == "__main__":
    show_protocol()