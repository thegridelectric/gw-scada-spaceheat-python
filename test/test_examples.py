# This should be an absolute import from package base: "gw_spaceheat...."
# That requires changes *all* imports to use absolute import, so we don't do this in this demo.
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
import load_house

# noinspection PyUnresolvedReferences
def test_imports():
    """Verify modules can be imported"""
    # note: disable warnings about local imports
    import actors.strategy_switcher
    import load_house

def test_load_house():
    """Verify that load_house() successfully loads test objects"""
    assert len(ShNode.by_alias) == 0
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    assert len(ShNode.by_alias) == 24
    nodes_w_components = list(filter(lambda x: x.primary_component_id is not None, ShNode.by_alias.values()))
    assert len(nodes_w_components) == 19
    actor_nodes_w_components = list(filter(lambda x: x.python_actor_name is not None, nodes_w_components))
    assert len(actor_nodes_w_components) == 7
    temp_sensor_nodes = list(filter(lambda x: isinstance(x.primary_component.cac, TempSensorCac), actor_nodes_w_components))
    # assert len(temp_sensor_nodes) ==

def test_run_temp_senors_demo():
    """Verify that the user-facing demo code runs. The purpose of this test is primarily to verify that users can run
    the demo without surprises, not to verify functionality. This might lead to test duplication, but it allows this test
    to be exactly or very close to the demo while another test deviate from demo to control testing functionality"""


