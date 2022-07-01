import sys
import argparse
import logging
from typing import Optional, Sequence, Dict, Callable, Tuple, List

import load_house
from actors.strategy_switcher import strategy_from_node
from data_classes.sh_node import ShNode

LOGGING_FORMAT = "%(asctime)s %(message)s"


def parse_args(
    argv: Optional[Sequence[str]] = None,
    default_nodes: Optional[Sequence[str]] = None,
) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--log", action="store_true", help="Turn logging on.")
    parser.add_argument(
        "-n", "--nodes", default=default_nodes or [], nargs="*", help="ShNode aliases to load."
    )
    return parser.parse_args(argv or sys.argv[1:])


def setup_logging(args: argparse.Namespace) -> None:
    """Setup python logging based on parsed command line args"""
    if args.log:
        level = "DEBUG"
    else:
        level = "INFO"
    logging.basicConfig(level=level, format=LOGGING_FORMAT)


def run_nodes(aliases: Sequence[str], logging_on: bool = False, dbg: Optional[Dict] = None) -> None:
    """Start actors associated with node aliases. If dbg is not None, the actor instances will be returned in dbg["actors"]
    as dict of alias:actor."""

    actor_constructors: List[Tuple[ShNode, Callable]] = []

    for alias in aliases:
        node = ShNode.by_alias[alias]
        actor_function = strategy_from_node(node)
        if not actor_function:
            raise ValueError(f"ERROR. Node alias [{alias}] has no strategy")
        actor_constructors.append((node, actor_function))

    actors = [constructor(node, logging_on=logging_on) for node, constructor in actor_constructors]

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
    setup_logging(args)
    load_house.load_all()
    run_nodes(args.nodes, logging_on=bool(args.log), dbg=dbg)
