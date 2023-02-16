import argparse
import sys
from typing import Optional
from typing import Sequence

import dotenv
from rich import print
from rich.table import Table
from rich.text import Text

from actors2.config import ScadaSettings
from command_line_utils import get_requested_aliases
from data_classes.hardware_layout import HardwareLayout
from schema.enums import ActorClass


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-e",
        "--env-file",
        default=".env",
        help=(
            "Name of .env file to locate with dotenv.find_dotenv(). Defaults to '.env'. "
            "Pass empty string in quotation marks to suppress use of .env file."
        ),
    )
    parser.add_argument(
        "-n",
        "--nodes",
        default=None,
        nargs="*",
        help="ShNode aliases to load.",
    )
    return parser.parse_args(sys.argv[1:] if argv is None else argv)


def show_layout(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    dotenv_file = dotenv.find_dotenv(args.env_file)
    settings = ScadaSettings(_env_file=dotenv_file)
    requested_aliases = get_requested_aliases(args)
    layout = HardwareLayout.load(
        settings.paths.hardware_layout,
        included_node_names=requested_aliases
    )
    print("Nodes:")
    print(layout.nodes)
    print("Component ids:")
    component_ids = {
        node.alias: node.component_id for node in layout.nodes.values()
    }
    print(component_ids)
    print("Node Components")
    node_components = {
        node.alias: layout.component(node.alias)
        for node in layout.nodes.values()
    }
    print(node_components)
    node_cacs = {
        node.alias: layout.cac(node.alias)
        for node in layout.nodes.values()
    }
    print("Node cacs")
    print(node_cacs)
    table = Table()
    table.add_column("Name", header_style="bold green", style="green")
    table.add_column("Component", header_style="bold dark_orange", style="dark_orange")
    table.add_column("Cac", header_style="bold red1", style="red1")
    table.add_column("Make/Model", header_style="bold gold1", style="gold1")
    table.add_column("Role", header_style="bold purple4", style="purple4")
    table.add_column("Actor", header_style="bold green1", style="green1")
    none_text = Text("None", style="cyan")
    for alias in layout.nodes:
        component = layout.component(alias)
        if component is None:
            component_txt = none_text
        else:
            component_txt = str(component.display_name)
        cac = layout.cac(alias)
        if cac is None:
            cac_txt = none_text
            make_model_text = none_text
        else:
            if cac.display_name:
                cac_txt = Text(cac.display_name, style=table.columns[2].style)
            else:
                cac_txt = Text(cac.component_attribute_class_id, style="deep_pink1")
            if hasattr(cac, "make_model"):
                make_model_text = Text(cac.make_model.value, style=table.columns[3].style)
            else:
                make_model_text = none_text
        node = layout.node(alias)
        if node.role:
            role_text = Text(node.role.value)
        else:
            role_text = none_text
        if node.actor_class and node.actor_class != ActorClass.NONE:
            actor_text = Text(node.actor_class.value)
        else:
            actor_text = none_text
        table.add_row(alias, component_txt, cac_txt, make_model_text, role_text, actor_text)
    print(table)
    # scada_node, actor_nodes = get_actor_nodes(requested_aliases, layout, Scada2.DEFAULT_ACTORS_MODULE)
    # scada = Scada2(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
    # return scada

if __name__ == "__main__":
    show_layout()