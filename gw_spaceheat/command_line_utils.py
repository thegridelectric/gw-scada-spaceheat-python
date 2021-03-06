import sys
import argparse
import logging
from typing import Optional, Sequence, Dict, Callable, Tuple, List

import dotenv

import load_house
from actors.strategy_switcher import strategy_from_node
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
