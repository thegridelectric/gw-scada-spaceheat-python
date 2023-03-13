from enums import Unit
from enums import TelemetryName

from schema import EgaugeRegisterConfig_Maker
from schema import TelemetryReportingConfig_Maker
from schema import EgaugeIo_Maker
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker


i = EgaugeRegisterConfig_Maker(
    address=9004,
    name="Garage power",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.elt1",
    nameplate_max_value=4500,
    sample_period_s=300,
    async_report_threshold=0.05,
    telemetry_name=TelemetryName.PowerW,
).tuple


boost_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple


comp = ElectricMeterComponentGt_Maker(
    component_id="245b8267-8a7c-45e0-b9ec-f7cd67cbe716",
    component_attribute_class_id="739a6e32-bb9c-43bc-a28d-fb61be665522",
    display_name="Apple Freedom EGauge meter",
    hw_uid="GC14050323",
    modbus_host="eGauge14875.local",
    modbus_port=502,
    egauge_io_list=[boost_io],
).tuple


d = comp.as_dict()
