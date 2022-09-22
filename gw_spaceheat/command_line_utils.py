import importlib
import sys
import argparse
from typing import Optional, Sequence, Dict, Callable, Tuple, List

import dotenv

import load_house
from logging_setup import setup_logging
from actors.strategy_switcher import strategy_from_node
from actors2 import Scada2
from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from schema.enums.role.sh_node_role_110 import Role

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
    update_root_logger: bool = True,
    dbg: Optional[Dict] = None,
) -> None:
    """Load and run the configured Nodes. If dbg is not None it will be populated with the actor objects."""
    args = parse_args(argv, default_nodes=default_nodes)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file))
    settings.paths.mkdirs()
    setup_logging(args, settings, update_root_logger)
    run_nodes(args.nodes, settings, load_house.load_all(settings), dbg=dbg)


async def run_async_actors(
    aliases: Sequence[str],
    settings: ScadaSettings,
    layout: HardwareLayout,
    actors_package_name: str = Scada2.DEFAULT_ACTORS_MODULE,
):
    actors_package = importlib.import_module(actors_package_name)
    scada_node: Optional[ShNode] = None
    actor_nodes = []

    for node in [layout.node(alias) for alias in aliases]:
        if not node.has_actor:
            raise ValueError(f"ERROR. Node {node.alias} has no actor.")
        if node.actor_class.value == "Scada":
            if scada_node is not None:
                raise ValueError(
                    "ERROR. Exactly 1 scada node must be present in alaises. Found at least two ("
                    f"{scada_node.alias} and {node.alias}"
                )
            scada_node = node
        elif not getattr(actors_package, node.actor_class.value):
            raise ValueError(
                f"ERROR. Actor class {node.actor_class.value} for node {node.alias} "
                f"not in actors package {actors_package_name}"
            )
        else:
            actor_nodes.append(node)

    scada = Scada2(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
    scada.start()
    try:
        await scada.run_forever()
    finally:
        scada.stop()


async def run_async_actors_main(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
    update_root_logger: bool = True,
):
    args = parse_args(argv, default_nodes=default_nodes)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file))
    settings.paths.mkdirs()
    setup_logging(args, settings, update_root_logger)
    layout = load_house.load_all(settings)
    if not args.nodes:
        args.nodes = [
            node.alias
            for node in filter(lambda x: (x.role != Role.ATN and x.role != Role.HOME_ALONE and x.has_actor), layout.nodes.values())
        ]
    await run_async_actors(args.nodes, settings, layout)
