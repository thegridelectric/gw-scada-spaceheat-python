from actors.config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.hardware_layout import HardwareLayout
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker


def test_electric_meter_component():
    settings = ScadaSettings()
    HardwareLayout.load(settings.paths.hardware_layout)
    d = {
        "ComponentId": "04ceb282-d7e8-4293-80b5-72455e1a5db3",
        "ComponentAttributeClassId": "c1856e62-d8c0-4352-b79e-6ae05a5294c2",
        "DisplayName": "Main power meter for Little orange house garage space heat",
        "HwUid": "9999",
        "ModbusHost": "eGauge4922.local",
        "ModbusPort": 502,
        "ConfigList": [],
        "EgaugeIoList": [],
        "TypeName": "electric.meter.component.gt",
        "Version": "100",
    }

    gw_tuple = ElectricMeterComponentGt_Maker.dict_to_tuple(d)
    assert gw_tuple.ComponentId in ElectricMeterComponent.by_id.keys()
    component_as_dc = ElectricMeterComponent.by_id[gw_tuple.ComponentId]
    assert gw_tuple.HwUid == "9999"
    assert component_as_dc.hw_uid == "35941_308"
