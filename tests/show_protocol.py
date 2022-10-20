"""Sample driver script showing message in/out summary lines for a portion of the mqtt protocol."""
import argparse
import enum
import logging
import sys
import time
import typing
from typing import List
from typing import Optional
from typing import Sequence

import dotenv
import load_house
from actors.actor_base import ActorBase
from actors.atn import Atn
from command_line_utils import add_default_args
from command_line_utils import setup_logging
from config import LoggerLevels
from config import LoggingSettings
from config import ScadaSettings
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from fragment_runner import FragmentRunner
from fragment_runner import ProtocolFragment
from fragment_runner import delimit
from fragment_runner import do_nothing
from utils import wait_for


# noinspection PyUnusedLocal
def i_am_quiet(self, note: str):
    """Replaces screen_print with silence"""
    pass


def please_be_quiet():
    """Monkey patch screen_print() to do nothing."""
    ActorBase.screen_print = i_am_quiet
    Atn.screen_print = i_am_quiet

class FragmentNames(enum.Enum):
    all = "all"
    meter = "meter"
    GsPwr = "GsPwr"
    thermo = "thermo"
    relay = "relay"
    relay_toggle = "relay_toggle"

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


def fragment_from_enum(runner: FragmentRunner, name: FragmentNames) -> "ProtocolFragment":
    if name == FragmentNames.all:
        fragment = AllFragments(runner)
    elif name == FragmentNames.thermo:
        fragment = ThermoFragment(runner)
    elif name == FragmentNames.meter:
        fragment = MeterFragment(runner)
    elif name == FragmentNames.GsPwr:
        fragment = GsPwrFragment(runner)
    elif name == FragmentNames.relay:
        fragment = RelayFragment(runner)
    elif name == FragmentNames.relay_toggle:
        fragment = RelayToggleFragment(runner)
    else:
        raise ValueError(f"Unknown fragment name {name}")
    return fragment


class WaitingFragment(ProtocolFragment):

    def __init__(self, runner: FragmentRunner):
        super().__init__(runner, wait_at_least=runner.wait_at_least)


class ThermoFragment(WaitingFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [self.runner.actors.scada, self.runner.actors.thermo]


class RelayFragment(WaitingFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [self.runner.actors.scada, self.runner.actors.relay]


class RelayToggleFragment(ProtocolFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [self.runner.actors.scada, self.runner.actors.relay]

    def run(self, *args, **kwargs):
        time.sleep(1)
        scada = self.runner.actors.scada
        relay = self.runner.actors.relay
        scada.turn_on(relay.node)
        time.sleep(1)
        scada.turn_off(relay.node)
        time.sleep(1)


class MeterFragment(WaitingFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [self.runner.actors.scada, self.runner.actors.meter]


class GsPwrFragment(ProtocolFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [self.runner.actors.scada, self.runner.actors.meter, self.runner.actors.atn]

    def run(self, *args, **kwargs):
        self.runner.actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
        num_sets = 10
        for i in range(num_sets):
            print(f"Setting GsPwr {i+1:2d}/{num_sets}")
            typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                self.runner.actors.meter.driver
            ).fake_power_w += 1000
            time.sleep(1)
        time.sleep(5)


class AllFragments(ProtocolFragment):

    def get_requested_actors(self) -> Sequence[ActorBase]:
        return [
            self.runner.actors.scada,
            self.runner.actors.atn,
            self.runner.actors.home_alone,
            self.runner.actors.relay,
            self.runner.actors.meter,
            self.runner.actors.thermo
        ]

    def run(self, *args, **kwargs):
        actors = self.runner.actors
        actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True

        do_nothing(self.runner.do_nothing_time)

        delimit("TURNING ON")
        actors.atn.turn_on(self.runner.layout.node("a.elt1.relay"))
        wait_for(lambda: actors.relay.relay_state == 1, 10, f"Relay state")
        delimit("TURNED ON")

        do_nothing(self.runner.do_nothing_time)

        delimit("REQUESTING STATUS")
        actors.atn.status()
        wait_for(
            lambda: actors.atn.snapshot_received > 0, 10, f"cli_resp_received == 0 {actors.atn.summary_str()}"
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

        do_nothing(self.runner.do_nothing_time)

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
    settings = ScadaSettings(
        _env_file=dotenv.find_dotenv(args.env_file),
        logging=LoggingSettings(
            levels=LoggerLevels(
                message_summary=logging.DEBUG
            )
        )
    )
    setup_logging(args, settings)
    please_be_quiet()
    load_house.load_all(settings)
    runner = FragmentRunner(
        settings,
        wait_at_least=args.wait_at_least,
        do_nothing_time=args.do_nothing_time,
    )
    if not args.fragments:
        args.fragments = ["all"]
    for fragment_name in args.fragments:
        runner.add_fragment(fragment_from_enum(runner, FragmentNames(fragment_name)))
    runner.run()


if __name__ == "__main__":
    show_protocol()