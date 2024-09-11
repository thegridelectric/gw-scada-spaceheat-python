import argparse
import sys
from pathlib import Path
from typing import Optional
from typing import Sequence

import dotenv
from gwproto.data_classes.components.hubitat_component import HubitatComponent
from gwproto.data_classes.components.hubitat_poller_component import HubitatPollerComponent
from gwproto.data_classes.components.hubitat_tank_component import HubitatTankComponent
from gwproto.data_classes.hardware_layout import LoadError
from rich import print
from rich.table import Table
from rich.text import Text

from actors import Scada
from actors.config import ScadaSettings
from command_line_utils import get_actor_nodes
from command_line_utils import get_requested_aliases
from gwproactor.config import MQTTClient
from gwproto.data_classes.errors import DataClassLoadingError
from gwproto.data_classes.hardware_layout import HardwareLayout
from enums import ActorClass


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
        "-l",
        "--layout-file",
        default=None,
        help=(
            "Name of layout file (e.g. hardware-layout.json or apple for apple.json). "
            "If path is relative it will be relative to settings.paths.config_dir. "
            "If path has no extension, .json will be assumed. "
            "If not specified default settings.paths.hardware_layout will be used."
        ),
    )
    parser.add_argument(
        "-n",
        "--nodes",
        default=None,
        nargs="*",
        help="ShNode aliases to load.",
    )
    parser.add_argument(
        "-r",
        "--raise-errors",
        action="store_true",
        help="Raise any errors immediately to see full call stack."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print additional information"
    )
    parser.add_argument(
        "-t",
        "--table-only",
        action="store_true",
        help="Print only the table"
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
        cac.ComponentAttributeClassId: cac.DisplayName
        for cac in layout.cacs.values()
    })
    print("Nodes:")
    print(layout.nodes)
    print("Raw nodes:")
    print([n["Alias"] for n in layout.layout["ShNodes"]])
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
    # unused components
    unused_components = dict(layout.components)
    for node in layout.nodes.values():
        unused_components.pop(node.component_id, None)
    print(f"Unused Components: {len(unused_components)}")
    if unused_components:
        print(unused_components)
    # unused cacs
    unused_cacs = dict(layout.cacs)
    for component in layout.components.values():
        unused_cacs.pop(component.component_attribute_class_id, None)
    print(f"Unused Cacs: {len(unused_cacs)}")
    if unused_cacs:
        print(unused_cacs)
    # dangling components
    dangling_component_nodes = set()
    for node in layout.nodes.values():
        if node.component_id and node.component_id not in layout.components:
            dangling_component_nodes.add(node.alias)
    print(f"Nodes with component_id but no component: {len(dangling_component_nodes)}")
    if dangling_component_nodes:
        print(sorted(dangling_component_nodes))
    # dangling cacs
    dangling_cac_components = set()
    for component in layout.components.values():
        if component.component_attribute_class_id and component.component_attribute_class_id not in layout.cacs:
            dangling_cac_components.add(component.display_name)
    print(f"Components with cac_id but no cac: {len(dangling_cac_components)}")
    if dangling_cac_components:
        print(sorted(dangling_cac_components))


def print_layout_members(
    layout: HardwareLayout,
    errors: Optional[list[LoadError]] = None,
) -> None:
    if errors is None:
        errors = []

    print("Layout identifier attributes")
    for attr in [
        "atn_g_node_alias",
        "atn_g_node_instance_id",
        "atn_g_node_id",
        "terminal_asset_g_node_alias",
        "terminal_asset_g_node_id",
        "scada_g_node_alias",
        "scada_g_node_id",
    ]:
        try:
            print(f"  {attr}: <{getattr(layout, attr)}>")
        except Exception as e:
            errors.append(LoadError(attr, {}, e))
    print("Layout named items")
    for attr in [
        "power_meter_component",
        "power_meter_cac",
        "power_meter_node",
        "scada_node",
        "home_alone_node",
        "my_home_alone",
    ]:
        try:
            item = getattr(layout, attr)
            display = None if item is None else item.display_name
            print(f"  {attr}: <{display}>")
        except Exception as e:
            errors.append(LoadError(attr, {}, e))


    print("Named layout collections:")
    for attr in [
        "all_nodes_in_agg_power_metering",
        "all_resistive_heaters",
        "my_boolean_actuators",
        "my_simple_sensors",
        "my_multipurpose_sensors",
    ]:
        print(f"  {attr}:")
        try:
            for entry in getattr(layout, attr):
                print(f"    <{entry.alias}>")
        except Exception as e:
            errors.append(LoadError(attr, {}, e))
    for tt_prop_name in [
        "all_multipurpose_telemetry_tuples",
        "all_power_meter_telemetry_tuples",
        "my_telemetry_tuples",
        "all_telemetry_tuples_for_agg_power_metering",
    ]:
        print(f"  {tt_prop_name}:")
        try:
            for tt in getattr(layout, tt_prop_name):
                print(f"    src: <{tt.SensorNode.alias}>  about: <{tt.AboutNode.alias}>")
        except Exception as e:
            errors.append(LoadError(tt_prop_name, {}, e))

def print_layout_urls(layout: HardwareLayout) -> None:
    url_dicts = {
        component.display_name: component.urls()
        for component in [
        component for component in layout.components.values()
        if isinstance(component, (HubitatComponent, HubitatTankComponent, HubitatPollerComponent))
    ]
    }
    if url_dicts:
        print("Component URLS:")
        for name, urls in url_dicts.items():
            print(f"  <{name}>:")
            for k, v in urls.items():
                print(f"    {k}: {str(v)}")


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
                component_txt = Text("MISSING", style="red") + \
                    Text(f" Component {node.component_id[:8]}", style=none_text.style)
            else:
                component_txt = none_text
        else:
            component_txt = str(component.display_name)
        cac = layout.cac(node.alias)
        if cac is None:
            make_model_text = none_text
            if component is not None and component.component_attribute_class_id:
                cac_txt = Text("MISSING", style="red") + \
                    Text(f" Cac {component.component_attribute_class_id[:8]}", style=none_text.style)
            else:
                cac_txt = none_text

        else:
            if cac.DisplayName:
                cac_txt = Text(cac.DisplayName, style=table.columns[2].style)
            else:
                cac_txt = Text("Cac id: ") + Text(cac.ComponentAttributeClassId, style="light_coral")
            if hasattr(cac, "make_model"):
                make_model_text = Text(str(cac.MakeModel), style=table.columns[3].style)
            else:
                make_model_text = none_text
        node = layout.node(node.alias)
        if node.role:
            role_text = Text(str(node.role.value))
        else:
            role_text = none_text
        if node.actor_class and node.actor_class != ActorClass.NoActor:
            actor_text = Text(str(node.actor_class.value))
        else:
            actor_text = none_text
        table.add_row(node.alias, component_txt, cac_txt, make_model_text, role_text, actor_text)
    print(table)

def try_scada_load(requested_aliases: Optional[set[str]], layout: HardwareLayout, settings: ScadaSettings, raise_errors: bool = False) -> Optional[Scada]:
    settings = settings.model_copy(deep=True)
    settings.paths.mkdirs()
    scada_node, actor_nodes = get_actor_nodes(requested_aliases, layout, Scada.DEFAULT_ACTORS_MODULE)
    scada = None
    for k, v in settings._iter():  # noqa
        if isinstance(v, MQTTClient):
            v.tls.use_tls = False
    try:
        scada = Scada(name=scada_node.alias, settings=settings, hardware_layout=layout, actor_nodes=actor_nodes)
    except (
            DataClassLoadingError,
            KeyError,
            ModuleNotFoundError,
            ValueError,
            FileNotFoundError,
            AttributeError,
            StopIteration,
    ) as e:
        print(f"ERROR loading Scada: <{e}> {type(e)}")
        print("Use '-r' to see full error stack.")
        if raise_errors:
            raise e
    return scada


def show_layout(
        layout: HardwareLayout,
        requested_aliases: Optional[set[str]],
        settings: ScadaSettings,
        raise_errors: bool = False,
        errors: Optional[list[LoadError]] = None,
        table_only: bool = False,
) -> Scada:
    if errors is None:
        errors = []
    if not table_only:
        print_component_dicts(layout)
        print_layout_members(layout, errors)
        print_layout_urls(layout)
    print_layout_table(layout)
    scada = try_scada_load(
        requested_aliases,
        layout,
        settings,
        raise_errors=raise_errors
    )
    return scada

def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    dotenv_file = dotenv.find_dotenv(args.env_file)
    print(f"Using .env file {dotenv_file}, exists: {Path(dotenv_file).exists()}")
    settings = ScadaSettings(_env_file=dotenv_file)
    if args.layout_file:
        layout_path = Path(args.layout_file)
        if Path(layout_path.name) == layout_path:
            layout_path = settings.paths.config_dir / layout_path
        if not layout_path.suffix:
            layout_path = layout_path.with_suffix(".json")
        settings.paths.hardware_layout = layout_path
    requested_aliases = get_requested_aliases(args)
    print(f"Using layout file: <{settings.paths.hardware_layout}>, exists: {settings.paths.hardware_layout.exists()}")
    errors = []
    layout = HardwareLayout.load(
        settings.paths.hardware_layout,
        included_node_names=requested_aliases,
        raise_errors=bool(args.raise_errors),
        errors=errors,
    )
    show_layout(
        layout,
        requested_aliases,
        settings,
        raise_errors=args.raise_errors,
        errors=errors,
        table_only=args.table_only,
    )
    if errors:
        print(f"\nFound {len(errors)} ERRORS in layout:")
        for i, error in enumerate(errors):
            print(f"  {i+1:2d}: {error.type_name:30s}  <{error.src_dict.get('DisplayName', '')}>  <{error.exception}> ")
            if args.verbose:
                print(f"  {i+1:2d}:  element:\n{error.src_dict}\n")
        print(f"\nFound {len(errors)} ERRORS in layout.")

if __name__ == "__main__":
    main()
