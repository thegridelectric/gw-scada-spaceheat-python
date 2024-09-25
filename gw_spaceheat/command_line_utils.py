import importlib
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional, Sequence, Tuple
import traceback

import dotenv
import rich

from gwproactor import setup_logging
from gwproactor.config import MQTTClient
from gwproactor.config.paths import TLSPaths
from pydantic import BaseModel

from actors import Scada
from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from enums import Role
from pydantic_settings import BaseSettings
from data_classes.house_0 import H0N

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
        default=ScadaSettings.model_fields["seconds_per_report"].default,
        help="Seconds per status report"
    )

    parser.add_argument(
        "-n",
        "--nodes",
        default=default_nodes or None,
        nargs="*",
        help="ShNode aliases to load.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print information without doing anything"
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

def get_requested_aliases(args: argparse.Namespace) -> Optional[set[str]]:
    if args.nodes is None:
        requested = None
    else:
        requested = set(args.nodes)
        requested.add(H0N.scada)
        requested.add(H0N.home_alone)
    return requested


def get_actor_nodes(requested_aliases: Optional[set[str]], layout: HardwareLayout, actors_package_name: str) -> Tuple[ShNode, list[ShNode]]:
    actors_package = importlib.import_module(actors_package_name)
    if requested_aliases:
        requested_nodes = [layout.node(alias) for alias in requested_aliases]
    else:
        requested_nodes = layout.nodes.values()
    actor_nodes = []
    scada_node: Optional[ShNode] = None
    for node in requested_nodes:
        if node.role not in [Role.Atn, Role.HomeAlone] and node.has_actor:
            if node.actor_class == "Scada":
                if scada_node is not None:
                    raise ValueError(
                        "ERROR. Exactly 1 scada node must be present in alaises. Found at least two ("
                        f"{node.alias} and {node.alias}"
                    )
                scada_node = node
            elif not getattr(actors_package, node.actor_class):
                raise ValueError(
                    f"ERROR. Actor class {node.actor_class} for node {node.alias} "
                    f"not in actors package {actors_package_name}"
                )
            else:
                actor_nodes.append(node)
    return scada_node, actor_nodes

def missing_tls_paths(paths: TLSPaths) -> list[tuple[str, Optional[Path]]]:
    missing = []
    for path_name in paths.model_fields:
        path = getattr(paths, path_name)
        if path is None or not Path(path).exists():
            missing.append((path_name, path))
    return missing

def check_tls_paths_present(model: BaseModel | BaseSettings, raise_error: bool = True) -> str:
    missing_str = ""
    for k, v in model._iter():  # noqa
        if isinstance(v, MQTTClient):
            if v.tls.use_tls:
                missing_paths = missing_tls_paths(v.tls.paths)
                if missing_paths:
                    missing_str += f"client {k}\n"
                    for path_name, path in missing_paths:
                        missing_str += f"  {path_name:20s}  {path}\n"
    if missing_str:
        error_str = f"ERROR. TLS usage requested but the following files are missing:\n{missing_str}"
        if raise_error:
            raise ValueError(error_str)
    else:
        error_str = ""
    return error_str

def get_scada(
    argv: Optional[Sequence[str]] = None,
    run_in_thread: bool = False,
    add_screen_handler: bool = True,
    actors_package_name: str = Scada.DEFAULT_ACTORS_MODULE,
) -> Scada:
    args = parse_args(argv)
    dotenv_file = dotenv.find_dotenv(args.env_file)
    dotenv_file_debug_str = f"Env file: <{dotenv_file}>  exists:{Path(dotenv_file).exists()}"
    settings = ScadaSettings(_env_file=dotenv_file)
    if args.dry_run:
        rich.print(dotenv_file_debug_str)
        rich.print(settings)
        missing_tls_paths_ = check_tls_paths_present(settings, raise_error=False)
        if missing_tls_paths_:
            rich.print(missing_tls_paths_)
        rich.print("Dry run. Doing nothing.")
        sys.exit(0)
    else:
        settings.paths.mkdirs()
        setup_logging(args, settings, add_screen_handler=add_screen_handler)
        logger = logging.getLogger(settings.logging.qualified_logger_names()["lifecycle"])
        logger.info("")
        logger.info(dotenv_file_debug_str)
        logger.info("Settings:")
        logger.info(settings.model_dump_json(indent=2))
        rich.print(settings)
        check_tls_paths_present(settings)
        requested_aliases = get_requested_aliases(args)
        layout = HardwareLayout.load(settings.paths.hardware_layout, included_node_names=requested_aliases)
        scada_node, actor_nodes = get_actor_nodes(requested_aliases, layout, actors_package_name)
        scada = Scada(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
        if run_in_thread:
            logger.info("run_async_actors_main() starting")
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
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        # noinspection PyBroadException
        try:
            exception_logger.exception(f"ERROR in run_async_actors_main. Shutting down: [{e}] / [{type(e)}]")
        except:  # noqa: E722
            traceback.print_exception(e)
        raise e
