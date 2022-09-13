"""Test code very similar to the scripts provided by the repo"""

import pytest

import load_house
from command_line_utils import run_nodes_main
from config import ScadaSettings
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role


@pytest.mark.parametrize(
    "aliases",
    [
        ["a.elt1.relay"],
        ["a.s"],
        ["a"],
    ],
)
def test_run_nodes_main(aliases):
    """Test command_line_utils.run_nodes_main()"""
    dbg = dict(actors={})
    try:
        run_nodes_main(
            argv=["-n", *aliases],
            dbg=dbg,
        )
        assert len(dbg["actors"]) == len(aliases)
    finally:
        for actor in dbg["actors"].values():
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass


def test_run_local():
    """Test the "run_local" script semantics"""
    layout = load_house.load_all(ScadaSettings())

    aliases = [
        node.alias
        for node in filter(lambda x: (x.role != Role.ATN and x.has_actor), layout.nodes.values())
    ]
    test_run_nodes_main(aliases)
