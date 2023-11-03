import time
from typing import Optional
import math

from aiohttp import ClientResponse
from aiohttp import ClientSession
from gwproactor import Actor
from gwproactor import Problems
from gwproactor import ServicesInterface
from gwproactor.actors.rest import RESTPoller
from gwproto import Message
from gwproto.data_classes.components.hubitat_tank_component import HubitatTankComponent
from gwproto.types.hubitat_tank_gt import FibaroTempSensorSettings
from pydantic import BaseModel
from pydantic import Extra
from result import Result

from actors.message import MultipurposeSensorTelemetryMessage
from drivers.exceptions import DriverError


class FibaroAttribute(BaseModel, extra=Extra.allow):
    name: str = ""
    currentValue: Optional[str | int | float] = None
    dataType: str = ""

class FibaroRefreshResponse(BaseModel, extra=Extra.allow):
    id: int
    name: str = ""
    label: str = ""
    type: str = ""
    attributes: list[FibaroAttribute]

    def get_attribute_by_name(self, name: str) -> Optional[FibaroAttribute]:
        return next((attr for attr in self.attributes if attr.name == name), None)

    def get_voltage(self) -> Optional[float]:
        attribute = self.get_attribute_by_name("voltage")
        if attribute is not None:
            try:
                return float(attribute.currentValue)
            except: # noqa
                pass
        return None



# 298 Kelvin is 25 Celcius
THERMISTOR_T0_DEGREES_KELVIN = 298
# NTC THermistors are 10 kOhms at 25 deg C
THERMISTOR_R0_OHMS = 10000
# NTC Thermistors have a "rated beta" on their data sheet
THERMISTOR_BETA = 3977
# Then, there is our pull-up resistor
VOLTAGE_DIVIDER_R_OHMS = 10000
# MAX_VOLTAGE = 23.7
# MAX_VOLTAGE = 11.75
FIBARO_PULLDOWN_OHMS = 150000

class HubitatTankError(DriverError):
    """Base class for hubitat tank module exceptions"""

class RFromV:
    """ Infer the resistance from the voltage measured from a TankModule Fibaro
    set up with no internal voltage divider and a pullup resistor.
    """
    voltage: float
    max_voltage: float
    r_both: Optional[float | BaseException] = None
    rt: Optional[float | BaseException] = None
    rd: int = int(VOLTAGE_DIVIDER_R_OHMS)
    fibaro_pulldown_ohms: int = FIBARO_PULLDOWN_OHMS

    def __init__(
        self,
        voltage: float,
        max_voltage: float,
        rd: int = VOLTAGE_DIVIDER_R_OHMS,
        fibaro_pulldown_ohms: int = FIBARO_PULLDOWN_OHMS,
    ):
        self.voltage = voltage
        self.max_voltage = max_voltage
        self.rd = int(rd)
        self.fibaro_pulldown_ohms = int(fibaro_pulldown_ohms)
        try:

            # r_both is the resistance of our thermistor in parallel with the
            # Fibaro pulldown
            self.r_both = self.rd * voltage / (max_voltage - voltage)
        except BaseException as e_r_both:
            self.r_both = e_r_both
        else:
            try:
                # Applying kirchoff
                numerator = self.fibaro_pulldown_ohms * self.r_both
                denominator = self.fibaro_pulldown_ohms - self.r_both
                self.rt = numerator / denominator
            except BaseException as e_rt:
                self.rt = e_rt

    def ok(self) -> bool:
        return isinstance(self.rt, float) and self.rt > 0

class TempCBeta:
    """We are using the beta formula instead of the Steinhart-Hart equation.
    Thermistor data sheets typically provide the three parameters needed
    for the beta formula (R0, beta, and T0) and do not provide the
    three parameters needed for the better beta function.
    "Under the best conditions, the beta formula is accurate to approximately
    +/- 1 C over the temperature range of 0 to 100C

    For more information go here:
    https://www.newport.com/medias/sys_master/images/images/hdb/hac/8797291479070/TN-STEIN-1-Thermistor-Constant-Conversions-Beta-to-Steinhart-Hart.pdf

    """

    r_from_v: RFromV | BaseException
    r0: int = THERMISTOR_R0_OHMS
    beta: int = THERMISTOR_BETA
    t0: int = THERMISTOR_T0_DEGREES_KELVIN
    log_rt_r0: Optional[float | BaseException] = None
    k: Optional[float | BaseException] = None
    c: Optional[float] = None

    def __init__(
        self,
        voltage: float,
        max_voltage: float,
        rd: int = VOLTAGE_DIVIDER_R_OHMS,
        fibaro_pulldown_ohms: int = FIBARO_PULLDOWN_OHMS,
        r0: int = THERMISTOR_R0_OHMS,
        beta: int = THERMISTOR_BETA,
        t0: int = THERMISTOR_T0_DEGREES_KELVIN,
    ):
        self.r0 = int(r0)
        self.beta = int(beta)
        self.t0 = int(t0)
        try:
            self.r_from_v = RFromV(
                voltage,
                max_voltage,
                rd=rd,
                fibaro_pulldown_ohms=fibaro_pulldown_ohms,
            )
        except BaseException as e_r_from_v:
            self.r_from_v = e_r_from_v
        else:
            if self.r_from_v.ok():
                try:
                    self.log_rt_r0 = math.log(self.r_from_v.rt / self.r0)
                except BaseException as e_log:
                    self.log_rt_r0 = e_log
                else:
                    try:
                        inv_k = (1 / self.t0) + (self.log_rt_r0 / self.beta)
                        self.k = 1 / inv_k
                    except BaseException as e_k:
                        self.k = e_k
                    else:
                        self.c = self.k - 273

    def ok(self) -> bool:
        return isinstance(self.c, float)

class FibaroTankTempPoller(RESTPoller):

    _last_read_time: float
    _report_src: str
    _report_dst: str
    _max_voltage: float
    _settings: FibaroTempSensorSettings

    def __init__(
            self,
            name: str,
            tank_module_name: str,
            sensor_supply_voltage: float,
            settings: FibaroTempSensorSettings,
            services: ServicesInterface
    ):
        self._report_src = tank_module_name
        self._report_dst = services.name
        self._max_voltage = sensor_supply_voltage
        self._settings = settings
        super().__init__(
            name,
            self._settings.rest,
            services.io_loop_manager,
            convert=self._converter,
            forward=services.send_threadsafe,
        )

    async def _make_request(self, session: ClientSession) -> Optional[ClientResponse]:
        """"A refresh sent to hubitat for fibaro returns the value of the *last* refresh,
        so we just send two refreshes.
        """
        response = await super()._make_request(session)
        if response is None:
            return None
        else:
            async with response:
                self._last_read_time = time.time()
            return await super()._make_request(session)

    async def _converter(self, response: ClientResponse) -> Optional[Message]:
        try:
            voltage = FibaroRefreshResponse(
                **await response.json()
            ).get_voltage()
            if voltage >= self._max_voltage:
                return None
            temp_c_beta = TempCBeta(voltage, self._max_voltage)
            if not temp_c_beta.ok():
                return None
            else:
                temp_c1000 = int(temp_c_beta.c * 1000)
                return MultipurposeSensorTelemetryMessage(
                    src=self._report_src,
                    dst=self._report_dst,
                    about_node_alias_list=[self._settings.node_name],
                    value_list=[temp_c1000],
                    telemetry_name_list=[self._settings.telemetry_name],
                )
        except BaseException as e:
            self._forward(
                Message(
                    Payload=Problems(errors=[e]).problem_event(
                        summary=(
                            f"Fibaro {self._settings.node_name} _convert() error "
                        ), src=self._report_src
                    )
                )
            )
        return None

class HubitatTankModule(Actor):

    _component: HubitatTankComponent
    _pollers: list[FibaroTankTempPoller]

    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        component = services.hardware_layout.component(name)
        if not isinstance(component, HubitatTankComponent):
            display_name = getattr(
                component, "display_name", "MISSING ATTRIBUTE display_name"
            )
            raise ValueError(
                f"ERROR. Component <{display_name}> has type {type(component)}. "
                f"Expected HubitatTankComponent.\n"
                f"  Node: {self.name}\n"
                f"  Component id: {component.component_id}"
            )

        super().__init__(name, services)
        self._component = component
        self._pollers = [
            FibaroTankTempPoller(
                name=device.node_name,
                tank_module_name=self.name,
                settings=device,
                services=services,
                sensor_supply_voltage=self._component.sensor_supply_voltage
            ) for device in self._component.devices
        ]

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        raise ValueError("HubitatTankModule does not currently process any messages")

    def start(self) -> None:
        for poller in self._pollers:
            poller.start()

    def stop(self) -> None:
        for poller in self._pollers:
            try:
                poller.stop()
            except: # noqa
                pass

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
