from actors2.config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.hardware_layout import HardwareLayout
from schema.gt.components import GtElectricMeterComponent_Maker


def test_electric_meter_component():
    settings = ScadaSettings()
    HardwareLayout.load(settings.paths.hardware_layout)
    d = {
        "ComponentId": "2bfd0036-0b0e-4732-8790-bc7d0536a85e",
        "DisplayName": "Main Power meter for Little orange house garage space heat",
        "ComponentAttributeClassId": "28897ac1-ea42-4633-96d3-196f63f5a951",
        "HwUid": "9999",
        "TypeAlias": "gt.electric.meter.component.100",
    }

    gw_tuple = GtElectricMeterComponent_Maker.dict_to_tuple(d)
    assert gw_tuple.ComponentId in ElectricMeterComponent.by_id.keys()
    component_as_dc = ElectricMeterComponent.by_id[gw_tuple.ComponentId]
    assert gw_tuple.HwUid == "9999"
    assert component_as_dc.hw_uid == "1001ab"
