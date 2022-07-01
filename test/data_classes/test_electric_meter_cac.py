import load_house
from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker


def test_electric_meter_cac():
    load_house.load_all()
    d = {
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "MakeModelGtEnumSymbol": "076da322",
        "DisplayName": "Gridworks Pm1 Simulated Power Meter",
        "LocalCommInterfaceGtEnumSymbol": "efc144cd",
        "UpdatePeriodMs": 1000,
        "TypeAlias": "gt.electric.meter.cac.100",
    }

    gw_tuple = GtElectricMeterCac_Maker.dict_to_tuple(d)
    assert gw_tuple.ComponentAttributeClassId in ElectricMeterCac.by_id.keys()
    dc = ElectricMeterCac.by_id[gw_tuple.ComponentAttributeClassId]

    assert dc.__repr__() == "Gridworks__SimPm1 Gridworks Pm1 Simulated Power Meter"
