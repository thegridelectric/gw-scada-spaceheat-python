import sys
import importlib
import importlib.util

from actors2.config import ScadaSettings
from data_classes.sh_node import ShNode
from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config_maker import (
    GtSensorReportingConfig_Maker as ConfigMaker,
)

from schema.enums.unit.unit_map import Unit
from schema.enums.make_model.make_model_map import MakeModel
from gwproto.enums import TelemetryName

from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent


class NodeConfig:
    """Shared configuration (for drivers and reporting) for simple sensors. These
    reporting configs will eventually be defaults, with values set from the AtomicTNode
    via Config messages.
    """

    def __init__(self, node: ShNode, settings: ScadaSettings):
        self.node = node
        component = node.component
        self.seconds_per_report = settings.seconds_per_report
        self.reporting = None
        self.driver = None
        self.typical_response_time_ms = 0
        if isinstance(component, BooleanActuatorComponent):
            self.set_boolean_actuator_config(component=component, settings=settings)
        elif isinstance(component, SimpleTempSensorComponent):
            self.set_simple_temp_sensor_config(component=component, settings=settings)
        elif isinstance(component, PipeFlowSensorComponent):
            self.set_pipe_flow_sensor_config(component=component, settings=settings)
        if self.reporting is None:
            raise Exception(f"Failed to set reporting config for {node}!")
        if self.driver is None:
            raise Exception(f"Failed to set driver for {node}")

    def __repr__(self):
        return f"Driver: {self.driver}. Reporting: {self.reporting}"

    def set_pipe_flow_sensor_config(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        cac = component.cac
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Pipe Flow sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=-2,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=TelemetryName.GALLONS_TIMES100,
            unit=Unit.GALLONS,
            async_report_threshold=None,
        ).tuple
        if cac.make_model == MakeModel.ATLAS__EZFLO:
            driver_module_name = "drivers.pipe_flow_sensor.atlas_ezflo__pipe_flow_sensor_driver"
            driver_class_name = "AtlasEzflo_PipeFlowSensorDriver"
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.pipe_flow_sensor.unknown_pipe_flow_sensor_driver"
            driver_class_name = "UnknownPipeFlowSensorDriver"
        else:
            raise NotImplementedError(f"No PipeTempSensor driver yet for {cac.make_model}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)

    def set_simple_temp_sensor_config(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        cac = component.cac
        self.typical_response_time_ms = cac.typical_response_time_ms
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Temp sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=cac.exponent,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=cac.telemetry_name,
            unit=cac.temp_unit,
            async_report_threshold=None,
        ).tuple
        if cac.make_model == MakeModel.ADAFRUIT__642:
            driver_module_name = "drivers.simple_temp_sensor.adafruit_642__simple_temp_sensor_driver"
            driver_class_name = "Adafruit642_SimpleTempSensorDriver"
        elif cac.make_model == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            driver_module_name = "drivers.simple_temp_sensor.gwsim__simple_temp_sensor_driver"
            driver_class_name = "Gwsim_SimpleTempSensorDriver"
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.simple_temp_sensor.unknown_simple_temp_sensor_driver"
            driver_class_name = "UnknownSimpleTempSensorDriver"
        else:
            raise NotImplementedError(f"No TempSensor driver yet for {cac.make_model}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)

    def set_boolean_actuator_config(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        cac = component.cac
        self.typical_response_time_ms = cac.typical_response_time_ms
        if self.node.reporting_sample_period_s is None:
            reporting_sample_period_s = self.seconds_per_report
        else:
            reporting_sample_period_s = self.node.reporting_sample_period_s
        self.reporting = ConfigMaker(
            report_on_change=True,
            exponent=0,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=reporting_sample_period_s,
            telemetry_name=cac.telemetry_name,
            unit=Unit.UNITLESS,
            async_report_threshold=0.5,
        ).tuple
        if cac.make_model == MakeModel.NCD__PR814SPST:
            found = importlib.util.find_spec("smbus2")
            if found:
                import smbus2 as smbus
                try:
                    smbus.SMBus(1)
                except FileNotFoundError:
                    found = False
            if found:
                driver_module_name = "drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver"
                driver_class_name = "NcdPr814Spst_BooleanActuatorDriver"
            else:
                driver_module_name = "drivers.boolean_actuator.unknown_boolean_actuator_driver import UnknownBooleanActuatorDriver"
                driver_class_name = "UnknownBooleanActuatorDriver"
        elif cac.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            driver_module_name = "drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver"
            driver_class_name = "GridworksSimBool30AmpRelay_BooleanActuatorDriver"
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.boolean_actuator.unknown_boolean_actuator_driver import UnknownBooleanActuatorDriver"
            driver_class_name = "UnknownBooleanActuatorDriver"
        else:
            raise NotImplementedError(f"No BooleanActuator driver yet for {cac.make_model}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)
