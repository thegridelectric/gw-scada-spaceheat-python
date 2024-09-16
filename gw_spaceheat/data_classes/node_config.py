import sys
import importlib
import importlib.util

from gwproto import ShNode

from actors.config import ScadaSettings
from gwproto.types import (
    PipeFlowSensorCacGt,
    RelayCacGt,
    SimpleTempSensorCacGt,
)

from gwtypes import GtSensorReportingConfig_Maker as ConfigMaker
from enums import Unit
from enums import MakeModel
from enums import TelemetryName

from gwproto.data_classes.components.relay_component import RelayComponent
from gwproto.data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from gwproto.data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent


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
        if isinstance(component, RelayComponent):
            self.set_relay_config(component=component, settings=settings)
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
        if not isinstance(cac, PipeFlowSensorCacGt):
            raise ValueError(f"ERROR. Pipe Flow Sensor must have cac of type PipeFlowSensorCacGt. Got {type(cac)}")
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Pipe Flow sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=-2,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=TelemetryName.GallonsTimes100,
            unit=Unit.Gallons,
            async_report_threshold=None,
        ).tuple
        if cac.MakeModel == MakeModel.ATLAS__EZFLO:
            driver_module_name = "drivers.pipe_flow_sensor.atlas_ezflo__pipe_flow_sensor_driver"
            driver_class_name = "AtlasEzflo_PipeFlowSensorDriver"
        elif cac.MakeModel == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.pipe_flow_sensor.unknown_pipe_flow_sensor_driver"
            driver_class_name = "UnknownPipeFlowSensorDriver"
        else:
            raise NotImplementedError(f"No PipeTempSensor driver yet for {cac.MakeModel}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)

    def set_simple_temp_sensor_config(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        cac = component.cac
        if not isinstance(cac, SimpleTempSensorCacGt):
            raise ValueError(f"ERROR. Simple Temp Sensor must have cac of type SimpleTempSensorCacGt. Got {type(cac)}")
        self.typical_response_time_ms = cac.TypicalResponseTimeMs
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Temp sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=cac.Exponent,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=cac.TelemetryName,
            unit=cac.TempUnit,
            async_report_threshold=None,
        ).tuple
        if cac.MakeModel == MakeModel.ADAFRUIT__642:
            driver_module_name = "drivers.simple_temp_sensor.adafruit_642__simple_temp_sensor_driver"
            driver_class_name = "Adafruit642_SimpleTempSensorDriver"
        elif cac.MakeModel == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            driver_module_name = "drivers.simple_temp_sensor.gwsim__simple_temp_sensor_driver"
            driver_class_name = "Gwsim_SimpleTempSensorDriver"
        elif cac.MakeModel == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.simple_temp_sensor.unknown_simple_temp_sensor_driver"
            driver_class_name = "UnknownSimpleTempSensorDriver"
        else:
            raise NotImplementedError(f"No TempSensor driver yet for {cac.MakeModel}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)

    def set_relay_config(self, component: RelayComponent, settings: ScadaSettings):
        cac = component.cac
        if not isinstance(cac, RelayCacGt):
            raise ValueError(f"ERROR. Relay must have cac of type RelayCacGt. Got {type(cac)}")
        self.typical_response_time_ms = cac.TypicalResponseTimeMs
        if self.node.reporting_sample_period_s is None:
            reporting_sample_period_s = self.seconds_per_report
        else:
            reporting_sample_period_s = self.node.reporting_sample_period_s
        self.reporting = ConfigMaker(
            report_on_change=True,
            exponent=0,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=reporting_sample_period_s,
            telemetry_name=TelemetryName.RelayState,
            unit=Unit.Unitless,
            async_report_threshold=0.5,
        ).tuple
        if cac.MakeModel == MakeModel.NCD__PR814SPST:
            found = importlib.util.find_spec("smbus2")
            if found:
                import smbus2 as smbus
                try:
                    smbus.SMBus(1)
                except FileNotFoundError:
                    found = False
            if found:
                driver_module_name = "drivers.relay.ncd__pr814spst__relay_driver"
                driver_class_name = "NcdPr814Spst_RelayDriver"
            else:
                driver_module_name = "drivers.relay.unknown_relay_driver"
                driver_class_name = "UnknownRelayDriver"
        elif cac.MakeModel == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            driver_module_name = "drivers.relay.gridworks_simbool30amprelay__relay_driver"
            driver_class_name = "GridworksSimBool30AmpRelay_RelayDriver"
        elif cac.MakeModel == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = "drivers.relay.unknown_relay_driver"
            driver_class_name = "UnknownRelayDriver"
        else:
            raise NotImplementedError(f"No BooleanActuator driver yet for {cac.MakeModel}")
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        self.driver = driver_class(component=component, settings=settings)
