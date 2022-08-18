import importlib
import sys
import argparse
import logging
from typing import Optional, Sequence, Dict, Callable, Tuple, List

import dotenv

import load_house
from actors.strategy_switcher import strategy_from_node
from actors2 import Scada2, ActorInterface
from config import ScadaSettings
from data_classes.sh_node import ShNode

LOGGING_FORMAT = "%(asctime)s %(message)s"

def add_default_args(
    parser: argparse.ArgumentParser,
    default_nodes: Optional[Sequence[str]] = None
) -> argparse.ArgumentParser:
    """Add default arguments to a command line parser"""
    parser.add_argument(
        "-e", "--env-file", default=".env",
        help=(
            "Name of .env file to locate with dotenv.find_dotenv(). Defaults to '.env'. "
            "Pass empty string in quotation marks to suppress use of .env file."
        ),
    )
    parser.add_argument("-l", "--log", action="store_true", help="Turn logging on.")
    parser.add_argument(
        "-n", "--nodes", default=default_nodes or [], nargs="*", help="ShNode aliases to load."
    )
    return parser

def parse_args(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
    args: Optional[argparse.Namespace] = None,
    parser: Optional[argparse.ArgumentParser] = None
) -> argparse.Namespace:
    """Parse command line arguments"""
    return add_default_args(
        parser or argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        default_nodes=default_nodes,
    ).parse_args(sys.argv[1:] if argv is None else argv, namespace=args)

def setup_logging(args: argparse.Namespace, settings: ScadaSettings) -> None:
    """Setup python logging based on parsed command line args"""
    if args.log or settings.logging_on:
        settings.logging_on = True
        level = "DEBUG"
    else:
        level = "INFO"
    logging.basicConfig(level=level, format=LOGGING_FORMAT)


def run_nodes(aliases: Sequence[str], settings: ScadaSettings, dbg: Optional[Dict] = None) -> None:
    """Start actors associated with node aliases. If dbg is not None, the actor instances will be returned in dbg["actors"]
    as dict of alias:actor."""

    actor_constructors: List[Tuple[ShNode, Callable]] = []

    for alias in aliases:
        node = ShNode.by_alias[alias]
        actor_function = strategy_from_node(node)
        if not actor_function:
            raise ValueError(f"ERROR. Node alias [{alias}] has no strategy")
        actor_constructors.append((node, actor_function))

    actors = [constructor(node, settings) for node, constructor in actor_constructors]

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
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file))
    setup_logging(args, settings)
    load_house.load_all(settings.world_root_alias)
    run_nodes(args.nodes, settings, dbg=dbg)

async def run_async_actors(
        aliases: Sequence[str],
        settings: ScadaSettings,
        actors_package_name: str = Scada2.DEFAULT_ACTORS_MODULE,
):
    actors_package = importlib.import_module(actors_package_name)
    nodes = [ShNode.by_alias[alias] for alias in aliases]
    scada_node:Optional[ShNode] = None
    actor_nodes = []

    for node in nodes:
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

    # TODO: Make choosing which actors to load more straight-forward and public.
    scada = Scada2(node=scada_node, settings=settings, actors=dict())
    for actor_node in actor_nodes:
        # noinspection PyProtectedMember
        scada._add_communicator(ActorInterface.load(actor_node, scada, actors_package_name))

    scada.start()
    await scada.run_forever()

async def run_async_actors_main(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
):
    if default_nodes is None:
        default_nodes = ["a.s", "a.elt1.relay"]
    args = parse_args(argv, default_nodes=default_nodes)
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file))
    setup_logging(args, settings)
    load_house.load_all(settings.world_root_alias)
    await run_async_actors(args.nodes, settings)