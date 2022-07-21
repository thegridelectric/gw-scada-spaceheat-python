from config import ScadaSettings
from test.utils import AbstractActor, flush_all
from data_classes.sh_node import ShNode

import pytest

from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker

from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import (
    GtElectricMeterComponent_Maker,
)

from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import SpaceheatNodeGt_Maker

from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver

from schema.enums.make_model.make_model_map import MakeModel


def test_abstract_actor():

    # Testing unknown meter driver
    flush_all()
    unknown_electric_meter_cac_dict = {
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "MakeModelGtEnumSymbol": "b6a32d9b",
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

    electric_meter_cac = GtElectricMeterCac_Maker.dict_to_dc(unknown_electric_meter_cac_dict)
    electric_meter_component = GtElectricMeterComponent_Maker.dict_to_dc(
        electric_meter_component_dict
    )

    SpaceheatNodeGt_Maker.dict_to_dc(meter_node_dict)

    assert electric_meter_component.cac == electric_meter_cac

    settings = ScadaSettings()
    abstract_actor = AbstractActor(node=ShNode.by_alias["a.m"], settings=settings)
    assert isinstance(abstract_actor.power_meter_driver(), UnknownPowerMeterDriver)
    flush_all()

    # Testing faulty meter driver (set to temp sensor)
    faulty_electric_meter_cac_dict = {
        "ComponentAttributeClassId": "f931a424-317c-4ca7-a712-55aba66070dd",
        "MakeModelGtEnumSymbol": "acd93fb3",
        "DisplayName": "Faulty Power Meter, actually an Adafruit temp sensor",
        "LocalCommInterfaceGtEnumSymbol": "829549d1",
        "TypeAlias": "gt.electric.meter.cac.100",
    }

    faulty_meter_component_dict = {
        "ComponentId": "03f7f670-4896-473f-8dda-521747ee7a2d",
        "DisplayName": "faulty meter, actually an Adafruit temp sensor",
        "ComponentAttributeClassId": "f931a424-317c-4ca7-a712-55aba66070dd",
        "HwUid": "bf0850e1",
        "TypeAlias": "gt.electric.meter.component.100",
    }

    meter_node_dict = {
        "Alias": "a.m",
        "RoleGtEnumSymbol": "9ac68b6e",
        "ActorClassGtEnumSymbol": "2ea112b9",
        "DisplayName": "Main Power Meter Little Orange House Test System",
        "ShNodeId": "e07e7632-0f3e-4a8c-badd-c6cb24926d85",
        "ComponentId": "03f7f670-4896-473f-8dda-521747ee7a2d",
        "TypeAlias": "spaceheat.node.gt.100",
    }

    electric_meter_cac = GtElectricMeterCac_Maker.dict_to_dc(faulty_electric_meter_cac_dict)
    GtElectricMeterComponent_Maker.dict_to_dc(faulty_meter_component_dict)
    SpaceheatNodeGt_Maker.dict_to_dc(meter_node_dict)
    assert electric_meter_cac.make_model == MakeModel.ADAFRUIT__642

    abstract_actor = AbstractActor(node=ShNode.by_alias["a.m"], settings=settings)
    with pytest.raises(Exception):
        abstract_actor.power_meter_driver()

    flush_all()
