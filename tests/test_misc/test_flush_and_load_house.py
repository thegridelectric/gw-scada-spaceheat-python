"""Test load_house module"""

from tests.utils import flush_all

from actors.config import ScadaSettings
from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.components.boolean_actuator_component import BooleanActuatorCac
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.components.electric_meter_component import ElectricMeterCac
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorCac
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from data_classes.components.resistive_heater_component import ResistiveHeaterCac
from data_classes.components.resistive_heater_component import ResistiveHeaterComponent
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorCac
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from enums import Role
from schema.gt.cacs import GtElectricMeterCac_Maker
from schema.gt.components import GtElectricMeterComponent_Maker
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import SpaceheatNodeGt_Maker


def test_flush_and_load_house():
    """Verify that flush_house() successfully removes all dictionary data from relevant dataclasses, and
    load_house() successfully loads test objects"""
    flush_all()

    unknown_electric_meter_cac_dict = {
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "MakeModelGtEnumSymbol": "00000000",
        "DisplayName": "Unknown Power Meter",
        "LocalCommInterfaceGtEnumSymbol": "829549d1",
        "TypeAlias": "gt.electric.meter.cac.100",
    }

    electric_meter_component_dict = {
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "DisplayName": "Test unknown meter",
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "HwUid": "7ec4a224",
        "TypeAlias": "gt.electric.meter.component.100",
    }

    meter_node_dict = {
        "Alias": "a.m",
        "RoleGtEnumSymbol": "9ac68b6e",
        "ActorClassGtEnumSymbol": "2ea112b9",
        "DisplayName": "Main Power Meter Little Orange House Test System",
        "ShNodeId": "c9456f5b-5a39-4a48-bb91-742a9fdc461d",
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "TypeAlias": "spaceheat.node.gt.100",
    }

    GtElectricMeterCac_Maker.dict_to_dc(unknown_electric_meter_cac_dict)
    GtElectricMeterComponent_Maker.dict_to_dc(electric_meter_component_dict)
    SpaceheatNodeGt_Maker.dict_to_dc(meter_node_dict)
    assert ShNode.by_id["c9456f5b-5a39-4a48-bb91-742a9fdc461d"].alias == "a.m"
    flush_all()

    layout = HardwareLayout.load(ScadaSettings().paths.hardware_layout)
    assert layout.node("a.m").sh_node_id == "0dd8a803-4724-4f49-b845-14ff57bdb3e6"
    for node in layout.nodes.values():
        layout.parent_node(node.alias)
    all_nodes = list(layout.nodes.values())
    assert len(all_nodes) == 26
    aliases = list(layout.nodes.keys())
    for i in range(len(aliases)):
        alias = aliases[i]
        assert layout.node(alias) is not None
    nodes_w_components = list(
        filter(lambda x: x.component_id is not None, layout.nodes.values())
    )
    assert len(nodes_w_components) == 20
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 13
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    assert len(tank_water_temp_sensor_nodes) == 5
    for node in tank_water_temp_sensor_nodes:
        assert node.reporting_sample_period_s is not None

    flush_all()
    assert BooleanActuatorComponent.by_id == {}
    assert ElectricMeterComponent.by_id == {}
    assert PipeFlowSensorComponent.by_id == {}
    assert ResistiveHeaterComponent.by_id == {}
    assert SimpleTempSensorComponent.by_id == {}
    assert Component.by_id == {}

    assert BooleanActuatorCac.by_id == {}
    assert ElectricMeterCac.by_id == {}
    assert PipeFlowSensorCac.by_id == {}
    assert ResistiveHeaterCac.by_id == {}
    assert SimpleTempSensorCac.by_id == {}
    assert ComponentAttributeClass.by_id == {}
    assert ShNode.by_id == {}


def test_load_real_house():
    layout = HardwareLayout(
        {"MyAtomicTNodeGNode": {"GNodeId": "d636cbeb-c4ad-45cd-b5bc-1c64cc33f4f4", "Alias": "w.isone.ct.newhaven.orange1", "DisplayName": "Little Orange House Garage Heating System AtomicTNode", "GNodeStatusValue": "Active", "PrimaryGNodeRoleAlias": "AtomicTNode"}, "MyTerminalAssetGNode": {"GNodeId": "137d7f06-ea65-4254-bfd1-5d56fa789229", "Alias": "w.isone.ct.newhaven.orange1.ta", "DisplayName": "Little Orange House Garage Heating System TerminalAsset", "GNodeStatusValue": "Active", "PrimaryGNodeRoleAlias": "TerminalAsset"}, "MyScadaGNode": {"GNodeId": "28817671-3899-4e24-a337-abcb8633e47a", "Alias": "w.isone.ct.newhaven.orange1.ta.scada", "DisplayName": "Little Orange House Garage Heating System SCADA", "GNodeStatusValue": "Active", "PrimaryGNodeRoleAlias": "Scada"}, "ShNodes": [{"Alias": "a", "RoleGtEnumSymbol": "6ddff83b", "ActorClassGtEnumSymbol": "b103058f", "DisplayName": "AtomicTNode", "ShNodeId": "7a4fe194-f572-407e-ab65-8d38f83d9eb0", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.home", "RoleGtEnumSymbol": "863e50d1", "ActorClassGtEnumSymbol": "32d3d19f", "DisplayName": "Little Orange House HomeAlone", "ShNodeId": "a1537de0-5c83-422e-9826-0995e0419953", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.s", "RoleGtEnumSymbol": "d0afb424", "ActorClassGtEnumSymbol": "6d37aa41", "DisplayName": "Little Orange House Main Scada", "ShNodeId": "19fc828e-0f9f-4a15-819b-6f02e38500c7", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.elt1", "RoleGtEnumSymbol": "99c5f326", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "First 4.5 kW boost in tank", "ShNodeId": "164d6c73-7c0c-4063-8cf9-01cde3a32b7c", "ComponentId": "26856174-e2b2-44f3-9f48-048201f1c0e8", "RatedVoltageV": 240, "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.elt1.relay", "RoleGtEnumSymbol": "57b788ee", "ActorClassGtEnumSymbol": "fddd0064", "DisplayName": "30A Relay for first boost element", "ShNodeId": "a9c94a2f-1800-4394-a90f-4f50dba053ac", "ComponentId": "57e2eb41-08f4-4032-8948-b14890fce9ca", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank", "RoleGtEnumSymbol": "3ecfe9b8", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Little Orange House Test Axeman Tank", "ShNodeId": "4ac89701-3472-4fb2-b404-8e3012af0399", "ComponentId": "780788df-9706-4299-b116-304a48838338", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.m", "RoleGtEnumSymbol": "9ac68b6e", "ActorClassGtEnumSymbol": "2ea112b9", "DisplayName": "Main Power Meter Little Orange House Test System", "ShNodeId": "55cecbdb-8a47-4160-a1d6-f3617a6279b4", "ComponentId": "04ceb282-d7e8-4293-80b5-72455e1a5db3", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out", "RoleGtEnumSymbol": "fe3cbdd5", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Main Heat Distribution Pipe Out of Tank", "ShNodeId": "1348b9cc-d45e-4095-aa39-24abb58a7498", "ComponentId": "71a224e5-8fa6-4af5-b4d0-ddbae4ca8b81", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.in", "RoleGtEnumSymbol": "fe3cbdd5", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Main Heat Distribution Pipe into Tank", "ShNodeId": "2aeb26f7-8251-431c-83b5-0ad3c0e4cff0", "ComponentId": "cdaa1c34-96d0-4713-9b89-c5b80b2668e6", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump", "RoleGtEnumSymbol": "b0eaf2ba", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Circulator Pump", "ShNodeId": "4dcf1be8-35ea-48c5-a7a0-9d74476b5a8d", "ComponentId": "5cbf2fd0-2987-42c6-99bf-2eaf1a17060b", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.relay", "RoleGtEnumSymbol": "57b788ee", "ActorClassGtEnumSymbol": "fddd0064", "DisplayName": "Circulator Pump Boolean Actuator", "ShNodeId": "d6109c64-daec-49b1-8b4f-1c69ab012e69", "ComponentId": "7de91fae-72ab-4226-8ebe-f66a9d85cea4", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.baseboard1", "RoleGtEnumSymbol": "05fdd645", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Single baseboard radiator", "ShNodeId": "9d8641f7-f5e2-4683-a427-5ebb18345b89", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.baseboard1.fan", "RoleGtEnumSymbol": "6896109b", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "First baseboard radiator fan", "ShNodeId": "57b3632f-df3e-4a7f-9205-1e6f953dece9", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.baseboard1.fan.relay", "RoleGtEnumSymbol": "57b788ee", "ActorClassGtEnumSymbol": "fddd0064", "DisplayName": "Relay for first baseboard radiator fan", "ShNodeId": "0223a903-ae99-4cd9-bd67-f28e1e799938", "ComponentId": "dd9a1452-d7aa-4523-8deb-8e302a4f86ba", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.baseboard1.garage", "RoleGtEnumSymbol": "65725f44", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "Little Orange House Garage", "ShNodeId": "e06809dc-7915-4389-9559-d4a89c3c4994", "ComponentId": "7b1e4102-7fb5-4048-93ae-312a12d47ba8", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.outdoors", "RoleGtEnumSymbol": "dd975b31", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "43 Avon St Microclimate", "ShNodeId": "7706f7ae-d01e-4ec2-89f4-8eb6fcc64f18", "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.flowmeter1", "RoleGtEnumSymbol": "ece3b600", "ActorClassGtEnumSymbol": "dae4b2f0", "DisplayName": "Flow Meter on distribution pipe out of tank", "ShNodeId": "0cb98277-b4b5-4016-8afa-ed2bffca6750", "ComponentId": "cec2fe5c-977c-4e5f-b299-f70adbc38523", "ReportingSamplePeriodS": 5, "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.temp1", "RoleGtEnumSymbol": "c480f612", "ActorClassGtEnumSymbol": "dae4b2f0", "DisplayName": "Temp Sensor on distribution pipe out of tank", "ShNodeId": "88b30858-65c0-470b-82e5-0981d3f2b5fe", "ComponentId": "2ca9e65a-5e85-4eaa-811b-901e940f8d09", "ReportingSamplePeriodS": 5, "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.in.temp1", "RoleGtEnumSymbol": "c480f612", "ActorClassGtEnumSymbol": "dae4b2f0", "DisplayName": "Temp Sensor on distribution pipe into tank", "ShNodeId": "675458cf-2da8-4792-8c50-e04c3f2f8326", "ComponentId": "35b5107c-bf32-4791-93eb-0497929fae57", "ReportingSamplePeriodS": 5, "TypeAlias": "spaceheat.node.gt.100"}, {
            "Alias": "a.tank.temp0", "RoleGtEnumSymbol": "73308a1f", "ActorClassGtEnumSymbol": "dae4b2f0", "DisplayName": "Tank temp sensor temp0 (on top)", "ShNodeId": "24e6c994-ff61-43b2-8550-d2017f413cb3", "ComponentId": "2d4b3b73-fc58-4789-b15e-9881f0b4ff40", "ReportingSamplePeriodS": 5, "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.tank.out.pump.baseboard1.garage.temp1", "RoleGtEnumSymbol": "fec74958", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "First Garage Temp sensor", "ShNodeId": "12b072ef-0a8b-4569-a055-12b486f35f04", "ComponentId": "38d2db8d-3668-4479-a839-c4b0298be270", "ReportingSamplePeriodS": 60, "TypeAlias": "spaceheat.node.gt.100"}, {"Alias": "a.outdoors.temp1", "RoleGtEnumSymbol": "5938bf1f", "ActorClassGtEnumSymbol": "99a5f20d", "DisplayName": "First Outdoor Temp sensor", "ShNodeId": "f0821873-e34f-4d53-a69a-10f6bed6d8d8", "ComponentId": "a9d43bb7-f838-4b7c-89ed-186eb8c89f23", "ReportingSamplePeriodS": 60, "TypeAlias": "spaceheat.node.gt.100"}], "ThermalEdges": [{"FromNodeAlias": "a.elt1", "ToNodeAlias": "a.tank"}, {"FromNodeAlias": "a.tank.in", "ToNodeAlias": "a.tank"}, {"FromNodeAlias": "a.tank", "ToNodeAlias": "a.tank.out"}, {"FromNodeAlias": "a.tank.out", "ToNodeAlias": "a.tank.out.pump"}, {"FromNodeAlias": "a.tank.out.pump", "ToNodeAlias": "a.tank.out.pump.baseboard1"}, {"FromNodeAlias": "a.tank.out.pump.baseboard1", "ToNodeAlias": "a.tank.in"}, {"FromNodeAlias": "a.tank.out.pump.baseboard1", "ToNodeAlias": "a.tank.out.pump.baseboard1.garage"}, {"FromNodeAlias": "a.tank.out.pump.baseboard1.garage", "ToNodeAlias": "a.outdoors"}], "ResistiveHeaterComponents": [{"ComponentId": "26856174-e2b2-44f3-9f48-048201f1c0e8", "DisplayName": "First 4.5 kW boost in tank", "ComponentAttributeClassId": "cf1f2587-7462-4701-b962-d2b264744c1d", "TypeAlias": "resistive.heater.component.gt.100", "MaxPowerW": 4500}], "BooleanActuatorComponents": [{"ComponentId": "dd9a1452-d7aa-4523-8deb-8e302a4f86ba", "DisplayName": "relay for radiator fan", "ComponentAttributeClassId": "c6e736d8-8078-44f5-98bb-d72ca91dc773", "Gpio": 1, "TypeAlias": "gt.boolean.actuator.component.100"}, {"ComponentId": "57e2eb41-08f4-4032-8948-b14890fce9ca", "DisplayName": "relay for first elt in tank", "ComponentAttributeClassId": "c6e736d8-8078-44f5-98bb-d72ca91dc773", "Gpio": 2, "TypeAlias": "gt.boolean.actuator.component.100"}, {"ComponentId": "7de91fae-72ab-4226-8ebe-f66a9d85cea4", "DisplayName": "relay for main circulator pump", "ComponentAttributeClassId": "c6e736d8-8078-44f5-98bb-d72ca91dc773", "Gpio": 3, "TypeAlias": "gt.boolean.actuator.component.100"}], "MultipurposeSensorComponents": [], "SimpleTempSensorComponents": [{"ComponentId": "a9d43bb7-f838-4b7c-89ed-186eb8c89f23", "DisplayName": "Outdoor Temperature Sensor", "ComponentAttributeClassId": "cac0f096-b460-4dce-aabf-a81ccce23566", "TypeAlias": "simple.temp.sensor.component.gt.100"}, {"ComponentId": "2ca9e65a-5e85-4eaa-811b-901e940f8d09", "DisplayName": "Temp sensor on pipe out of tank", "ComponentAttributeClassId": "43564cd2-0e78-41a2-8b67-ad80c02161e8", "HwUid": "00033ffe", "TypeAlias": "simple.temp.sensor.component.gt.000"}, {"ComponentId": "35b5107c-bf32-4791-93eb-0497929fae57", "DisplayName": "Temp sensor on pipe into tank", "ComponentAttributeClassId": "43564cd2-0e78-41a2-8b67-ad80c02161e8", "HwUid": "000363a9", "TypeAlias": "simple.temp.sensor.component.gt.000"}, {"ComponentId": "2d4b3b73-fc58-4789-b15e-9881f0b4ff40", "DisplayName": "Component for a.tank.temp0 (on top)", "ComponentAttributeClassId": "43564cd2-0e78-41a2-8b67-ad80c02161e8", "HwUid": "00041d3f", "TypeAlias": "simple.temp.sensor.component.gt.000"}, {"ComponentId": "38d2db8d-3668-4479-a839-c4b0298be270", "DisplayName": "First garage temp sensor", "ComponentAttributeClassId": "5450e92e-8c11-4383-b9b1-c8f412d83608", "TypeAlias": "simple.temp.sensor.component.gt.000"}], "ElectricMeterComponents": [{"ComponentId": "04ceb282-d7e8-4293-80b5-72455e1a5db3", "DisplayName": "Main power meter for Little orange house garage space heat", "ComponentAttributeClassId": "a3d298fb-a4ef-427a-939d-02cc9c9689c1", "HwUid": "35941_308", "TypeAlias": "gt.electric.meter.component.100"}], "PipeFlowSensorComponents": [{"ComponentId": "cec2fe5c-977c-4e5f-b299-f70adbc38523", "DisplayName": "Flow meter on pipe out of tank", "ComponentAttributeClassId": "14e7105a-e797-485a-a304-328ecc85cd98", "TypeAlias": "pipe.flow.sensor.component.gt.000"}], "OtherComponents": [{"ComponentId": "780788df-9706-4299-b116-304a48838338", "DisplayName": "Little Orange house Axeman Tank", "ComponentAttributeClassId": "683c193a-bf83-4491-a294-c0e32865a407"}, {"ComponentId": "71a224e5-8fa6-4af5-b4d0-ddbae4ca8b81", "DisplayName": "Hydronic pipe out of tank", "ComponentAttributeClassId": "cec0cb71-77bf-48a6-b644-2dcf124ac9fa"}, {"ComponentId": "cdaa1c34-96d0-4713-9b89-c5b80b2668e6", "DisplayName": "Hydronic pipe into tank", "ComponentAttributeClassId": "cec0cb71-77bf-48a6-b644-2dcf124ac9fa"}, {"ComponentId": "5cbf2fd0-2987-42c6-99bf-2eaf1a17060b", "DisplayName": "Circulator Pump", "ComponentAttributeClassId": "f9a35cca-2b6d-418d-a81f-81f1c3d64776"}, {"ComponentId": "7b1e4102-7fb5-4048-93ae-312a12d47ba8", "DisplayName": "Little Orange House garage", "ComponentAttributeClassId": "c884aafe-99e0-4468-8bff-ffa74f672f9d"}], "ResistiveHeaterCacs": [{"ComponentAttributeClassId": "cf1f2587-7462-4701-b962-d2b264744c1d", "MakeModelGtEnumSymbol": "00000000", "DisplayName": "Orange Garage heating element", "NameplateMaxPowerW": 4500, "RatedVoltageV": 240, "TypeAlias": "resistive.heater.cac.gt.100"}], "BooleanActuatorCacs": [{"ComponentAttributeClassId": "c6e736d8-8078-44f5-98bb-d72ca91dc773", "MakeModelGtEnumSymbol": "fabfa505", "TypicalResponseTimeMs": 200, "TypeAlias": "gt.boolean.actuator.cac.100"}], "PipeFlowSensorCacs": [{"ComponentAttributeClassId": "14e7105a-e797-485a-a304-328ecc85cd98", "MakeModelGtEnumSymbol": "00000000", "TypeAlias": "pipe.flow.sensor.cac.gt.000"}], "ElectricMeterCacs": [{"ComponentAttributeClassId": "a3d298fb-a4ef-427a-939d-02cc9c9689c1", "MakeModelGtEnumSymbol": "d300635e", "DisplayName": "Schneider Electric Iem3455 Power Meter", "LocalCommInterfaceGtEnumSymbol": "a6a4ac9f", "UpdatePeriodMs": 1000, "DefaultBaud": 9600, "TypeAlias": "gt.electric.meter.cac.100"}], "MultipurposeSensorCacs": [], "SimpleTempSensorCacs": [{"ComponentAttributeClassId": "43564cd2-0e78-41a2-8b67-ad80c02161e8", "MakeModelGtEnumSymbol": "acd93fb3", "DisplayName": "Adafruit High Temp Waterproof DS18B20 Digital Temp Sensor", "CommsMethod": "OneWire", "Exponent": -3, "TelemetryNameGtEnumSymbol": "c89d0ba1", "TempUnitGtEnumSymbol": "ec14bd47", "TypicalResponseTimeMs": 880, "TypeAlias": "simple.temp.sensor.cac.gt.000"}, {"ComponentAttributeClassId": "5450e92e-8c11-4383-b9b1-c8f412d83608", "MakeModelGtEnumSymbol": "00000000", "TempUnitGtEnumSymbol": "ec14bd47", "TelemetryNameGtEnumSymbol": "c89d0ba1", "TypicalResponseTimeMs": 0, "Exponent": -3, "TypeAlias": "simple.temp.sensor.cac.gt.000"}, {"ComponentAttributeClassId": "cac0f096-b460-4dce-aabf-a81ccce23566", "MakeModelGtEnumSymbol": "00000000", "TempUnitGtEnumSymbol": "ec14bd47", "TelemetryNameGtEnumSymbol": "c89d0ba1", "TypicalResponseTimeMs": 0, "Exponent": -3, "TypeAlias": "simple.temp.sensor.cac.gt.000"}], "OtherCacs": [{"ComponentAttributeClassId": "683c193a-bf83-4491-a294-c0e32865a407", "MakeModelGtEnumSymbol": "00000000"}, {"ComponentAttributeClassId": "cec0cb71-77bf-48a6-b644-2dcf124ac9fa", "MakeModelGtEnumSymbol": "00000000"}, {"ComponentAttributeClassId": "f9a35cca-2b6d-418d-a81f-81f1c3d64776", "MakeModelGtEnumSymbol": "00000000"}, {"ComponentAttributeClassId": "c884aafe-99e0-4468-8bff-ffa74f672f9d", "MakeModelGtEnumSymbol": "00000000"}]}
    )
    for node in layout.nodes.values():
        layout.parent_node(node.alias)
