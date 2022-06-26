import load_house
import pytest
from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.errors import DcError
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker
from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import (
    GtElectricMeterComponent_Maker,
)


def test_electric_meter_cac():
    load_house.load_all()
    d = {
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "MakeModelGtEnumSymbol": "076da322",
        "DisplayName": "Gridworks Pm1 Simulated Power Meter",
        "LocalCommInterfaceGtEnumSymbol": "efc144cd",
        "UpdatePeriodMs": 500,
    }

    meter_cac_as_tuple = GtElectricMeterCac_Maker.dict_to_tuple(d)
    assert meter_cac_as_tuple.ComponentAttributeClassId in ElectricMeterCac.by_id.keys()
    meter_cac_as_dc = ElectricMeterCac.by_id[meter_cac_as_tuple.ComponentAttributeClassId]
    assert meter_cac_as_dc.update_period_ms == 1000
    assert meter_cac_as_tuple.UpdatePeriodMs == 500

    with pytest.raises(DcError):
        meter_cac_as_dc.update(gw_tuple=meter_cac_as_tuple)

    d2 = {
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "MakeModelGtEnumSymbol": "076da322",
        "DisplayName": "Gridworks Pm1 Eletric Meter",
        "LocalCommInterfaceGtEnumSymbol": "efc144cd",
        "UpdatePeriodMs": 1000,
    }

    meter_cac_2_as_tuple = GtElectricMeterCac_Maker.dict_to_tuple(d2)
    assert meter_cac_as_dc.display_name != meter_cac_2_as_tuple.DisplayName
    meter_cac_as_dc.update(gw_tuple=meter_cac_2_as_tuple)


def test_electric_meter_component():
    load_house.load_all()
    d = {
        "ComponentId": "2bfd0036-0b0e-4732-8790-bc7d0536a85e",
        "DisplayName": "Main Power meter for Little orange house garage space heat",
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "HwUid": "9999",
    }

    gw_tuple = GtElectricMeterComponent_Maker.dict_to_tuple(d)
    assert gw_tuple.ComponentId in ElectricMeterComponent.by_id.keys()
    component_as_dc = ElectricMeterComponent.by_id[gw_tuple.ComponentId]
    assert gw_tuple.HwUid == "9999"
    assert component_as_dc.hw_uid == "1001ab"

    with pytest.raises(DcError):
        component_as_dc.update(gw_tuple=gw_tuple)
