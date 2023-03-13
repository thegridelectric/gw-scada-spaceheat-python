from enums import TelemetryName, Unit
from schema import (EgaugeIo_Maker, EgaugeRegisterConfig_Maker,
                    TelemetryReportingConfig_Maker)
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker

config_list = []
i = EgaugeRegisterConfig_Maker(
    address=9012,
    name="07 Spacepak HP",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.heatpump",
    nameplate_max_value=4500,
    sample_period_s=300,
    async_report_threshold=0.05,
    telemetry_name=TelemetryName.PowerW,
).tuple

config_list.append(o)
hp_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple

i = EgaugeRegisterConfig_Maker(
    address=9016,
    name="08 Electric resistance tank",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.tank1.elts",
    nameplate_max_value=9000,
    sample_period_s=300,
    async_report_threshold=0.05,
    telemetry_name=TelemetryName.PowerW,
).tuple

config_list.append(o)

boost_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple

i = EgaugeRegisterConfig_Maker(
    address=9020,
    name="09 Wilo/ Spacepak glycol pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.heatpump.condensorloopsource.pump",
    nameplate_max_value=90,
    sample_period_s=300,
    async_report_threshold=0.05,
    telemetry_name=TelemetryName.PowerW,
).tuple

config_list.append(o)

glycol_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple

i = EgaugeRegisterConfig_Maker(
    address=9024,
    name="10 GF/ HX pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.hxpump",
    nameplate_max_value=180,
    sample_period_s=300,
    async_report_threshold=0.2,
    telemetry_name=TelemetryName.PowerW,
).tuple
config_list.append(o)

hx_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple

i = EgaugeRegisterConfig_Maker(
    address=9028,
    name="11 GF/ Distribution pump",
    description="change in value",
    type="f32",
    denominator=1,
    unit="W",
).tuple

o = TelemetryReportingConfig_Maker(
    report_on_change=True,
    exponent=1,
    unit=Unit.W,
    about_node_name="a.distsourcewater.pump",
    nameplate_max_value=180,
    sample_period_s=300,
    async_report_threshold=0.2,
    telemetry_name=TelemetryName.PowerW,
).tuple

config_list.append(o)

dist_pump_io = EgaugeIo_Maker(input_config=i, output_config=o).tuple


comp = ElectricMeterComponentGt_Maker(
    component_id="8d2be3c8-2ea8-4cb4-8f56-96de9a73ca48",
    component_attribute_class_id="739a6e32-bb9c-43bc-a28d-fb61be665522",
    display_name="Apple Freedom EGauge meter",
    hw_uid="BP00679",
    modbus_host="eGauge4922.local",
    modbus_port=502,
    config_list=config_list,
    egauge_io_list=[hp_io, boost_io, glycol_io, hx_io, dist_pump_io],
).tuple


d = comp.as_dict()
