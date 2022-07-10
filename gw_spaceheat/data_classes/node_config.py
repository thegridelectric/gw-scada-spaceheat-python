from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
import settings
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import (
    GridworksSimBool30AmpRelay_BooleanActuatorDriver,
)
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import (
    NcdPr814Spst_BooleanActuatorDriver,
)
from drivers.boolean_actuator.unknown_boolean_actuator_driver import UnknownBooleanActuatorDriver
from drivers.pipe_flow_sensor.unknown_pipe_flow_sensor_driver import UnknownPipeFlowSensorDriver
from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver
from drivers.power_meter.schneiderelectric_iem3455__power_meter_driver import (
    SchneiderElectricIem3455_PowerMeterDriver,
)
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from drivers.temp_sensor.adafruit_642__temp_sensor_driver import Adafruit642_TempSensorDriver
from drivers.temp_sensor.gridworks_water_temp_high_precision_temp_sensor_driver import (
    GridworksWaterTempSensorHighPrecision_TempSensorDriver,
)
from drivers.temp_sensor.unknown_temp_sensor_driver import UnknownTempSensorDriver
from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config_maker import (
    GtSensorReportingConfig_Maker as ConfigMaker,
)
from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config_maker import GtEqReportingConfig_Maker
from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config_maker import (
    GtPowermeterReportingConfig_Maker as PowerConfigMaker,
)
from schema.enums.unit.unit_map import Unit
from schema.enums.make_model.make_model_map import MakeModel


from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from data_classes.components.temp_sensor_component import TempSensorComponent


class NodeConfig:
    """Much of the state data here should eventually be set by a reporting contract with the
    AtomicTNode; with the values here being default values. However, some of the values are
    physical characteristics of nodes - e.g., the max value of power for a boost element. These
    come from houses.json
    """

    FASTEST_POWER_METER_POLL_PERIOD_MS = 40

    def __init__(self, node: ShNode):
        self.node = node
        component = node.component
        self.reporting = None
        self.driver = None
        self.typical_response_time_ms = 0
        if isinstance(node.component, BooleanActuatorComponent):
            self.set_boolean_actuator_config(component=component)
        elif isinstance(node.component, ElectricMeterComponent):
            self.set_electric_meter_config(component=component)
        elif isinstance(node.component, TempSensorComponent):
            self.set_temp_sensor_config(component=component)
        elif isinstance(node.component, PipeFlowSensorComponent):
            self.set_pipe_flow_sensor_config(component=component)
        if self.reporting is None:
            raise Exception(f"Failed to set reporting config for {node}!")
        if self.driver is None:
            raise Exception(f"Failed to set driver for {node}")

    def __repr__(self):
        return f"Driver: {self.driver}. Reporting: {self.reporting}"

    def set_electric_meter_config(self, component: ElectricMeterComponent):
        cac = component.cac
        eq_reporting_config_list = []
        current_config = GtEqReportingConfig_Maker(
            sh_node_alias="a.elt1",
            report_on_change=True,
            telemetry_name=TelemetryName.CURRENT_RMS_MICRO_AMPS,
            unit=Unit.AMPS_RMS,
            exponent=6,
            sample_period_s=settings.SCADA_REPORTING_PERIOD_S,
            async_report_threshold=0.02,
        ).tuple

        eq_reporting_config_list.append(current_config)

        power_config = GtEqReportingConfig_Maker(
            sh_node_alias="a.elt1",
            report_on_change=True,
            telemetry_name=TelemetryName.POWER_W,
            unit=Unit.W,
            exponent=0,
            sample_period_s=settings.SCADA_REPORTING_PERIOD_S,
            async_report_threshold=0.02,
        ).tuple

        eq_reporting_config_list.append(power_config)
        poll_period_ms = max(self.FASTEST_POWER_METER_POLL_PERIOD_MS, cac.update_period_ms)
        self.reporting = PowerConfigMaker(
            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
            poll_period_ms=poll_period_ms,
            hw_uid=component.hw_uid,
            electrical_quantity_reporting_config_list=eq_reporting_config_list,
        ).tuple

        if cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownPowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            self.driver = SchneiderElectricIem3455_PowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMPM1:
            self.driver = GridworksSimPm1_PowerMeterDriver(component=component)
        else:
            raise NotImplementedError(f"No ElectricMeter driver yet for {cac.make_model}")

    def set_pipe_flow_sensor_config(self, component: PipeFlowSensorComponent):
        cac = component.cac
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Temp sensor node {self.node} is missing ReportingSamplePeriodS!")
        pass
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=5,
            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=cac.telemetry_name,
            unit=Unit.GPM,
            async_report_threshold=None,
        ).tuple
        if cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownPipeFlowSensorDriver(component=component)
        else:
            raise NotImplementedError(f"No PipeTempSensor driver yet for {cac.make_model}")

    def set_temp_sensor_config(self, component: TempSensorComponent):
        cac = component.cac
        self.typical_response_time_ms = cac.typical_response_time_ms
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Temp sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting = ConfigMaker(
            report_on_change=False,
            exponent=cac.exponent,
            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
            sample_period_s=self.node.reporting_sample_period_s,
            telemetry_name=cac.telemetry_name,
            unit=cac.temp_unit,
            async_report_threshold=None,
        ).tuple
        if cac.make_model == MakeModel.ADAFRUIT__642:
            self.driver = Adafruit642_TempSensorDriver(component=component)
        elif cac.make_model == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            self.driver = GridworksWaterTempSensorHighPrecision_TempSensorDriver(
                component=component
            )
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownTempSensorDriver(component=component)
        else:
            raise NotImplementedError(f"No TempSensor driver yet for {cac.make_model}")

    def set_boolean_actuator_config(self, component: BooleanActuatorComponent):
        cac = component.cac
        self.typical_response_time_ms = cac.typical_response_time_ms
        if self.node.reporting_sample_period_s is None:
            reporting_sample_period_s = settings.SCADA_REPORTING_PERIOD_S
        else:
            reporting_sample_period_s = self.node.reporting_sample_period_s
        self.reporting = ConfigMaker(
            report_on_change=True,
            exponent=0,
            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
            sample_period_s=reporting_sample_period_s,
            telemetry_name=cac.telemetry_name,
            unit=Unit.UNITLESS,
            async_report_threshold=0.5,
        ).tuple

        if cac.make_model == MakeModel.NCD__PR814SPST:
            self.driver = NcdPr814Spst_BooleanActuatorDriver(component=component)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver = GridworksSimBool30AmpRelay_BooleanActuatorDriver(component=component)
        elif cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            self.driver = UnknownBooleanActuatorDriver(component=component)
        else:
            raise NotImplementedError(f"No BooleanActuator driver yet for {cac.make_model}")
