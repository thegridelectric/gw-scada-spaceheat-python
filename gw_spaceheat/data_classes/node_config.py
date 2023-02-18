from actors2.config import ScadaSettings
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import (
    GridworksSimBool30AmpRelay_BooleanActuatorDriver,
)
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import (
    NcdPr814Spst_BooleanActuatorDriver,
)
from drivers.boolean_actuator.unknown_boolean_actuator_driver import UnknownBooleanActuatorDriver
from drivers.pipe_flow_sensor.unknown_pipe_flow_sensor_driver import UnknownPipeFlowSensorDriver
from drivers.pipe_flow_sensor.atlas_ezflo__pipe_flow_sensor_driver import AtlasEzflo_PipeFlowSensorDriver
from drivers.simple_temp_sensor.adafruit_642__simple_temp_sensor_driver import Adafruit642_SimpleTempSensorDriver
from drivers.simple_temp_sensor.gwsim__simple_temp_sensor_driver import (
    Gwsim_SimpleTempSensorDriver,
)
from drivers.simple_temp_sensor.unknown_simple_temp_sensor_driver import UnknownSimpleTempSensorDriver
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
        if isinstance(node.component, BooleanActuatorComponent):
            self.set_boolean_actuator_config(component=component, settings=settings)
        elif isinstance(node.component, SimpleTempSensorComponent):
            self.set_simple_temp_sensor_config(component=component, settings=settings)
        elif isinstance(node.component, PipeFlowSensorComponent):
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
        pass
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=-2,
            reporting_period_s=self.seconds_per_report,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=TelemetryName.WATER_FLOW_GPM_TIMES100,
            unit=Unit.GPM,
            async_report_threshold=None,
        ).tuple
        if cac.make_model == MakeModel.ATLAS__EZFLO:
            self.driver = AtlasEzflo_PipeFlowSensorDriver(component=component, settings=settings)
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownPipeFlowSensorDriver(component=component, settings=settings)
        else:
            raise NotImplementedError(f"No PipeTempSensor driver yet for {cac.make_model}")

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
            self.driver = Adafruit642_SimpleTempSensorDriver(component=component, settings=settings)
        elif cac.make_model == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            self.driver = Gwsim_SimpleTempSensorDriver(
                component=component, settings=settings
            )
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownSimpleTempSensorDriver(component=component, settings=settings)
        else:
            raise NotImplementedError(f"No TempSensor driver yet for {cac.make_model}")

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
            self.driver = NcdPr814Spst_BooleanActuatorDriver(component=component, settings=settings)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver = GridworksSimBool30AmpRelay_BooleanActuatorDriver(component=component, settings=settings)
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownBooleanActuatorDriver(component=component, settings=settings)
        else:
            raise NotImplementedError(f"No BooleanActuator driver yet for {cac.make_model}")
