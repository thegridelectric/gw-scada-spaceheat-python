from actors.config import ScadaSettings
from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.hardware_layout import HardwareLayout
from schema import ElectricMeterCacGt_Maker


def test_electric_meter_cac():
    settings = ScadaSettings()
    HardwareLayout.load(settings.paths.hardware_layout)
    d = {
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "MakeModelGtEnumSymbol": "076da322",
        "DisplayName": "Gridworks Pm1 Simulated Power Meter",
        "InterfaceGtEnumSymbol": "efc144cd",
        "PollPeriodMs": 1000,
        "TelemetryNameList": ["af39eec9"],
        "TypeName": "electric.meter.cac.gt",
        "Version": "000",
    }

    gw_tuple = ElectricMeterCacGt_Maker.dict_to_tuple(d)
    assert gw_tuple.ComponentAttributeClassId in ElectricMeterCac.by_id.keys()
    dc = ElectricMeterCac.by_id[gw_tuple.ComponentAttributeClassId]

    assert dc.__repr__() == "GRIDWORKS__SIMPM1 Gridworks Pm1 Simulated Power Meter"
