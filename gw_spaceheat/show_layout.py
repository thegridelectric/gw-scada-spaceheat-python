import argparse
import sys
from pathlib import Path
from typing import Optional
from typing import Sequence

import dotenv
from rich import print
from rich.table import Table
from rich.text import Text

from actors2 import Scada2
from actors2.config import ScadaSettings
from command_line_utils import get_actor_nodes
from command_line_utils import get_requested_aliases
from data_classes.errors import DataClassLoadingError
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

def print_component_dicts(layout: HardwareLayout):
    print("All Components:")
    print({
        component.component_id: component.display_name
        for component in layout.components.values()
    })
    print("All Cacs:")
    print({
        cac.component_attribute_class_id: cac.display_name
        for cac in layout.cacs.values()
    })
    print("Nodes:")
    print(layout.nodes)
    print("Node Component ids:")
    print({
        node.alias: node.component_id for node in layout.nodes.values()
    })
    print("Node Components")
    print({
        node.alias: layout.component(node.alias)
        for node in layout.nodes.values()
    })
    print("Node Cacs:")
    print({
        node.alias: layout.cac(node.alias)
        for node in layout.nodes.values()
    })
    dangling_component_nodes = set()
    for node in layout.nodes.values():
        if node.component_id and not node.component_id in layout.components:
            dangling_component_nodes.add(node.alias)
    if dangling_component_nodes:
        print("Nodes with component_id but no component:")
        print(sorted(dangling_component_nodes))
    dangling_cac_components = set()
    for node in layout.nodes.values():
        component = layout.component(node.alias)
        if component and component.component_attribute_class_id and not component.component_attribute_class_id in layout.cacs:
            dangling_cac_components.add(component.display_name)
    if dangling_cac_components:
        print("Components with cac id but not cac:")
        print(sorted(dangling_cac_components))

def print_layout_table(layout: HardwareLayout):
    table = Table()
    table.add_column("Name", header_style="bold green", style="green")
    table.add_column("Component", header_style="bold dark_orange", style="dark_orange")
    table.add_column("Cac", header_style="bold dark_orange", style="dark_orange")
    table.add_column("Make/Model", header_style="bold dark_orange", style="dark_orange")
    table.add_column("Role", header_style="bold purple4", style="purple4")
    table.add_column("Actor", header_style="bold green1", style="green1")
    none_text = Text("None", style="cyan")
    for node in layout.nodes.values():
        component = layout.component(node.alias)
        if component is None:
            if node.component_id:
                component_txt = Text("MISSING", style="red") + Text(f" Component {node.component_id[:8]}", style=none_text.style)
            else:
                component_txt = none_text
        else:
            component_txt = str(component.display_name)
        cac = layout.cac(node.alias)
        if cac is None:
            make_model_text = none_text
            if component is not None and component.component_attribute_class_id:
                cac_txt = Text("MISSING", style="red") + Text(f" Cac {component.component_attribute_class_id[:8]}", style=none_text.style)
            else:
                cac_txt = none_text

        else:
            if cac.display_name:
                cac_txt = Text(cac.display_name, style=table.columns[2].style)
            else:
                cac_txt = Text(f"Cac id: ") + Text(cac.component_attribute_class_id, style="light_coral")
            if hasattr(cac, "make_model"):
                make_model_text = Text(cac.make_model.value, style=table.columns[3].style)
            else:
                make_model_text = none_text
        node = layout.node(node.alias)
        if node.role:
            role_text = Text(node.role.value)
        else:
            role_text = none_text
        if node.actor_class and node.actor_class != ActorClass.NONE:
            actor_text = Text(node.actor_class.value)
        else:
            actor_text = none_text
        table.add_row(node.alias, component_txt, cac_txt, make_model_text, role_text, actor_text)
    print(table)

def try_scada_load(requested_aliases: Optional[set[str]], layout: HardwareLayout, settings: ScadaSettings) -> Optional[Scada2]:
    settings.paths.mkdirs()
    scada_node, actor_nodes = get_actor_nodes(requested_aliases, layout, Scada2.DEFAULT_ACTORS_MODULE)
    scada = None
    try:
        scada = Scada2(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
    except (DataClassLoadingError, KeyError) as e:
        print(f"ERROR loading Scada2: <{e}> {type(e)}")
    return scada

def show_layout(layout:HardwareLayout, requested_aliases: Optional[set[str]], settings: ScadaSettings) -> Scada2:
    print_component_dicts(layout)
    print_layout_table(layout)
    return try_scada_load(requested_aliases, layout, settings)


def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    dotenv_file = dotenv.find_dotenv(args.env_file)
    print(f"Using .env file {dotenv_file}, exists: {Path(dotenv_file).exists()}")
    settings = ScadaSettings(_env_file=dotenv_file)
    requested_aliases = get_requested_aliases(args)
    print(f"Using layout file: {settings.paths.hardware_layout}, exists: {settings.paths.hardware_layout.exists()}")
    layout = HardwareLayout.load(
        settings.paths.hardware_layout,
        included_node_names=requested_aliases
    )
    show_layout(layout, requested_aliases, settings)

if __name__ == "__main__":
    main()