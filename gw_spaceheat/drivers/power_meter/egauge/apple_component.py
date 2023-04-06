from schema.egauge_register_config import EgaugeRegisterConfig_Maker
from schema.telemetry_reporting_config import TelemetryReportingConfig_Maker
from schema.egauge_io import EgaugeIo_Maker
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker
from gwproto.enums import TelemetryName
from enums import Unit


boost_i = EgaugeRegisterConfig_Maker(
    address=9016,
    name="08 Electric resistance tank",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

boost_o = TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.PowerW,
    about_node_name="a.tank1.elts",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 9000
).tuple

boost_io = EgaugeIo_Maker(
    input_config=boost_i,
    output_config=boost_o
).tuple

heatpump_i = EgaugeRegisterConfig_Maker(
    address=9012,
    name="07 Spacepak HP",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

heatpump_o = TelemetryReportingConfig_Maker(
    telemetry_name=TelemetryName.PowerW,
    about_node_name="a.heatpump",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 3500
).tuple

heatpump_io = EgaugeIo_Maker(
    input_config=heatpump_i,
    output_config=heatpump_o
).tuple

dist_pump_i = EgaugeRegisterConfig_Maker(
    address=9028,
    name="11 GF/Distribution pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

dist_pump_o = TelemetryReportingConfig_Maker(
telemetry_name=TelemetryName.PowerW,
    about_node_name="a.distsourcewater.pump",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value= 95
).tuple

dist_pump_io = EgaugeIo_Maker(
    input_config=dist_pump_i,
    output_config=dist_pump_o
).tuple

glycol_pump_i = EgaugeRegisterConfig_Maker(
    address=9020,
    name="09 Wilo/ Spacepak glycol pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

glycol_pump_o = TelemetryReportingConfig_Maker(
telemetry_name=TelemetryName.PowerW,
    about_node_name="a.heatpump.condensorloopsource.pump",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value=185
).tuple

glycol_pump_io = EgaugeIo_Maker(
    input_config=glycol_pump_i,
    output_config=glycol_pump_o
).tuple

hx_pump_i = EgaugeRegisterConfig_Maker(
    address=9024,
    name="11 GF/HX pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W"
).tuple

hx_pump_o = TelemetryReportingConfig_Maker(
telemetry_name=TelemetryName.PowerW,
    about_node_name="a.hxpump",
    report_on_change=True,
    sample_period_s=300,
    exponent=0,
    unit=Unit.W,
    async_report_threshold=0.02,
    nameplate_max_value=185
).tuple

hx_pump_io = EgaugeIo_Maker(
    input_config=hx_pump_i,
    output_config=hx_pump_o
).tuple



comp = ElectricMeterComponentGt_Maker(
    component_id="8d2be3c8-2ea8-4cb4-8f56-96de9a73ca48",
    component_attribute_class_id="739a6e32-bb9c-43bc-a28d-fb61be665522",
    display_name="Apple Freedom EGauge meter",
    hw_uid="BP00679",
    modbus_host="eGauge4922.local",
    modbus_port=502,
    config_list = [boost_o, heatpump_o, dist_pump_o, glycol_pump_o, hx_pump_o],
    egauge_io_list=[boost_io, heatpump_io,dist_pump_io, glycol_pump_io, hx_pump_io]
).tuple


comp.as_type()
