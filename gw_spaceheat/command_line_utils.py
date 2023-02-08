import importlib
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional, Sequence, Dict, Callable, Tuple, List
import traceback

import dotenv
import rich

import load_house
from logging_setup import setup_logging
from actors.strategy_switcher import strategy_from_node
from actors2 import Scada2
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from schema.enums import Role

LOGGING_FORMAT = "%(asctime)s %(message)s"


def add_default_args(
    parser: argparse.ArgumentParser, default_nodes: Optional[Sequence[str]] = None
) -> argparse.ArgumentParser:
    """Add default arguments to a command line parser"""
    parser.add_argument(
        "-e",
        "--env-file",
        default=".env",
        help=(
            "Name of .env file to locate with dotenv.find_dotenv(). Defaults to '.env'. "
            "Pass empty string in quotation marks to suppress use of .env file."
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase logging verbosity")
    parser.add_argument("--message-summary", action="store_true", help="Turn on message summary logging")
    parser.add_argument(
        "--seconds-per-report",
        default=ScadaSettings.__fields__["seconds_per_report"].default,
        help="Seconds per status report"
    )

    parser.add_argument(
        "-n",
        "--nodes",
        default=default_nodes or [],
        nargs="*",
        help="ShNode aliases to load.",
    )
    return parser


def parse_args(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
    args: Optional[argparse.Namespace] = None,
    parser: Optional[argparse.ArgumentParser] = None,
) -> argparse.Namespace:
    """Parse command line arguments"""
    return add_default_args(
        parser
        or argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        ),
        default_nodes=default_nodes,
    ).parse_args(sys.argv[1:] if argv is None else argv, namespace=args)

def run_nodes(
    aliases: Sequence[str], settings: ScadaSettings, layout: HardwareLayout, dbg: Optional[Dict] = None
) -> None:
    """Start actors associated with node aliases. If dbg is not None, the actor instances will be returned in dbg["actors"]
    as dict of alias:actor."""

    actor_constructors: List[Tuple[ShNode, Callable]] = []

    for alias in aliases:
        node = layout.node(alias)
        actor_function = strategy_from_node(node)
        if not actor_function:
            raise ValueError(f"ERROR. Node alias [{alias}] has no strategy")
        actor_constructors.append((node, actor_function))

    actors = [constructor(node.alias, settings, layout) for node, constructor in actor_constructors]

    for actor in actors:
        actor.start()

    if dbg is not None:
        dbg["actors"] = {actor.node.alias: actor for actor in actors}


def run_nodes_main(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
    dbg: Optional[Dict] = None,
) -> None:
    """Load and run the configured Nodes. If dbg is not None it will be populated with the actor objects."""
    args = parse_args(argv, default_nodes=default_nodes)
    settings = ScadaSettings(
        _env_file=dotenv.find_dotenv(args.env_file),
        seconds_per_report=args.seconds_per_report,
    )
    settings.paths.mkdirs()
    setup_logging(args, settings)
    run_nodes(args.nodes, settings, load_house.load_all(settings), dbg=dbg)

def _get_requested_aliases(args: argparse.Namespace) -> set[str]:
    if args.nodes is None:
        requested = set()
    else:
        requested = set(args.nodes)
        requested.add("a.s")
        requested.add("a.home")
    return requested

def _get_actor_nodes(requested_aliases: set[str], layout: HardwareLayout, actors_package_name: str) -> Tuple[ShNode, list[ShNode]]:
    actors_package = importlib.import_module(actors_package_name)
    if requested_aliases:
        requested_nodes = [layout.node(alias) for alias in requested_aliases]
    else:
        requested_nodes = layout.nodes.values()
    actor_nodes = []
    scada_node: Optional[ShNode] = None
    for node in requested_nodes:
        if node.role not in [Role.ATN, Role.HOME_ALONE] and node.has_actor:
            if node.actor_class.value == "Scada":
                if scada_node is not None:
                    raise ValueError(
                        "ERROR. Exactly 1 scada node must be present in alaises. Found at least two ("
                        f"{node.alias} and {node.alias}"
                    )
                scada_node = node
            elif not getattr(actors_package, node.actor_class.value):
                raise ValueError(
                    f"ERROR. Actor class {node.actor_class.value} for node {node.alias} "
                    f"not in actors package {actors_package_name}"
                )
            else:
                actor_nodes.append(node)
    return scada_node, actor_nodes

def get_scada(
    argv: Optional[Sequence[str]] = None,
    run_in_thread: bool = False,
    add_screen_handler: bool = True,
    actors_package_name: str = Scada2.DEFAULT_ACTORS_MODULE,
) -> Scada2:
    args = parse_args(argv)
    dotenv_file = dotenv.find_dotenv(args.env_file)
    settings = ScadaSettings(_env_file=dotenv_file)
    settings.paths.mkdirs()
    setup_logging(args, settings, add_screen_handler=add_screen_handler)
    logger = logging.getLogger(settings.logging.qualified_logger_names()["lifecycle"])
    logger.info("")
    logger.info("run_async_actors_main() starting")
    logger.info("Env file: [%s]  exists:%s", dotenv_file, Path(dotenv_file).exists())
    logger.info("Settings:")
    logger.info(settings.json(sort_keys=True, indent=2))
    rich.print(settings)
    requested_aliases = _get_requested_aliases(args)
    layout = HardwareLayout.load(settings.paths.hardware_layout, included_node_names=requested_aliases)
    scada_node, actor_nodes = _get_actor_nodes(requested_aliases, layout, actors_package_name)
    scada = Scada2(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
    if run_in_thread:
        scada.run_in_thread()
    return scada

async def run_async_actors_main(argv: Optional[Sequence[str]] = None):
    exception_logger = logging.getLogger(ScadaSettings().logging.base_log_name)
    try:
        scada = get_scada(argv)
        exception_logger = scada.logger
        try:
            await scada.run_forever()
        finally:
            scada.stop()
    except BaseException as e:
        # noinspection PyBroadException
        try:
            exception_logger.exception("ERROR in run_async_actors_main. Shutting down")
        except:
            traceback.print_exception(e)
        raise e