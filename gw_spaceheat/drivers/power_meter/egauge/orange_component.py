from schema.egauge_register_config import EgaugeRegisterConfig_Maker
from schema.telemetry_reporting_config import TelemetryReportingConfig_Maker
from schema.egauge_io import EgaugeIo_Maker
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker
from gwproto.enums import TelemetryName
from enums import Unit


boost_i = EgaugeRegisterConfig_Maker(
    address=9004,
    name="Boost Power",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

boost_o = TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.PowerW,
    about_node_name="a.elt1",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 5000
).tuple

boost_io = EgaugeIo_Maker(
    input_config=boost_i,
    output_config=boost_o
).tuple



pump_i = EgaugeRegisterConfig_Maker(
    address=9006,
    name="Pump Power",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

pump_o = TelemetryReportingConfig_Maker(
telemetry_name=TelemetryName.PowerW,
    about_node_name="a.tank.out.pump",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 60
).tuple

pump_io = EgaugeIo_Maker(
    input_config=pump_i,
    output_config=pump_o
).tuple


config_list = [boost_o, pump_o]

comp = ElectricMeterComponentGt_Maker(
    component_id="245b8267-8a7c-45e0-b9ec-f7cd67cbe716",
    component_attribute_class_id="739a6e32-bb9c-43bc-a28d-fb61be665522",
    display_name="EGauge power meter for Little orange house garage space heat",
    hw_uid="GC14050323",
    modbus_host="eGauge14875.local",
    modbus_port=502,
    config_list = [boost_o, pump_o],
    egauge_io_list=[boost_io, pump_io]
).tuple

c = ElectricMeterComponentGt_Maker.tuple_to_dc(comp)

pwr1 = TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.PowerW,
    about_node_name="a.elt1",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 4500
).tuple

amp1 =  TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.CurrentRmsMicroAmps,
    about_node_name="a.elt1",
    report_on_change=True,
    sample_period_s=300,
    exponent=6,
    unit=Unit.AmpsRms,
    async_report_threshold=0.02,
    nameplate_max_value= 18750000
).tuple

pwr2 = TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.PowerW,
    about_node_name="a.elt2",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 4500
).tuple

comp = ElectricMeterComponentGt_Maker(
    component_id="2bfd0036-0b0e-4732-8790-bc7d0536a85e",
    component_attribute_class_id="28897ac1-ea42-4633-96d3-196f63f5a951",
    display_name="Power Meter for Simulated Test system",
    hw_uid="35941_308",
    modbus_host=None,
    modbus_port=None,
    config_list = [pwr1, amp1, pwr2],
    egauge_io_list=[]
).tuple