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


def r_from_v(voltage: float, max_voltage: float) -> float:
    """ Infer the resistance from the voltage measured from a TankModule1 Fibaro
    set up with no internal voltage divider and a 10K pullup resistor.
    """
    # rd = None # noqa
    # r_both = None
    # rt = None
    try:
        rd: int = int(VOLTAGE_DIVIDER_R_OHMS)

        # r_both is the resistance of our thermistor in parallel with the
        # Fibaro pulldown
        r_both = rd * voltage / (max_voltage - voltage)

        # Applying kirchoff
        rt = (FIBARO_PULLDOWN_OHMS * r_both) / (FIBARO_PULLDOWN_OHMS - r_both)
    except BaseException as e:
        # import rich
        # rich.print(f"r_from_v: {type(e)} <{e}>")
        raise e
    # finally:
    #     import rich
    #     rich.print(f"r_from_v:")
    #     rich.print(f"  voltage: {voltage}")
    #     rich.print(f"  max_voltage: {max_voltage}")
    #     rich.print(f"  rd: {rd}")
    #     rich.print(f"  rd * voltage: {rd * voltage}")
    #     rich.print(f"  (max_voltage - voltage): {(max_voltage - voltage)}")
    #     rich.print(f"  r_both: {r_both}")
    #     rich.print(f"  (FIBARO_PULLDOWN_OHMS * r_both): {(FIBARO_PULLDOWN_OHMS * r_both)}")
    #     rich.print(f"  (FIBARO_PULLDOWN_OHMS - r_both): {(FIBARO_PULLDOWN_OHMS - r_both)}")
    #     rich.print(f"  rt: {rt}")
    return rt


# """
#         voltage (float): The voltage measured between the thermistor and the
#         voltage divider resistor
#         max_voltage (float): The max voltage measurable by the sensor.
# """
def thermistor_temp_c_beta_formula(
        # voltage: float,
        # max_voltage: float,
        rt: float,
) -> float:
    """We are using the beta formula instead of the Steinhart-Hart equation.
    Thermistor data sheets typically provide the three parameters needed
    for the beta formula (R0, beta, and T0) and do not provide the
    three parameters needed for the better beta function.
    "Under the best conditions, the beta formula is accurate to approximately
    +/- 1 C over the temperature range of 0 to 100C

    For more information go here:
    https://www.newport.com/medias/sys_master/images/images/hdb/hac/8797291479070/TN-STEIN-1-Thermistor-Constant-Conversions-Beta-to-Steinhart-Hart.pdf

    Args:
        rt: calculated resistance

    Returns:
        float: The temperature getting measured by the thermistor in degrees Celcius
    """
    beta = None # noqa
    t0 = None # noqa
    # rt = None # noqa
    temp_c = None # noqa
    try:
        r0: int = int(THERMISTOR_R0_OHMS)
        beta: int = int(THERMISTOR_BETA)
        t0: int = int(THERMISTOR_T0_DEGREES_KELVIN)
        # Calculate the temperature in degrees Celsius. Note that 273 is
        # 0 degrees Celcius as measured in Kelvin.
        temp_c = 1 / ((1 / t0) + (math.log(rt / r0) / beta)) - 273
    except BaseException as e:
        # import rich
        # rich.print(f"thermistor_temp_c_beta_formula: {type(e)} <{e}>")
        # rich.print(f"  voltage: {voltage}")
        # rich.print(f"  max_voltage: {max_voltage}")
        # rich.print(f"  r0: {r0}") # noqa
        # rich.print(f"  beta: {beta}")
        # rich.print(f"  t0: {t0}")
        # rich.print(f"  rt: {rt}")
        # try:
        #     rich.print(f"  (1 / t0): {(1 / t0)}")
        # except BaseException as e2:
        #     print(f"  1 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  rt / r0: {rt / r0}")
        # except BaseException as e2:
        #     print(f"  2 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  math.log(rt / r0): {math.log(rt / r0)}")
        # except BaseException as e2:
        #     print(f"  3 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  1/k: {((1 / t0) + (math.log(rt / r0) / beta))}")
        # except BaseException as e2:
        #     print(f"  4 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  k: {1/((1 / t0) + (math.log(rt / r0) / beta))}")
        # except BaseException as e2:
        #     print(f"  5 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  c1: {1 / ((1 / t0) + (math.log(rt / r0) / beta)) - 273}")
        # except BaseException as e2:
        #     print(f"  6 WHOOPS: {type(e2)}  <{e2}>")
        # try:
        #     rich.print(f"  c2: {temp_c}")
        # except BaseException as e2:
        #     print(f"  7 WHOOPS: {type(e2)}  <{e2}>")
        raise e
    return temp_c

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
            convert=self._convert,
            forward=services.send_threadsafe,
        )

    async def _make_request(self, session: ClientSession) -> ClientResponse:
        """"A refresh sent to hubitat for fibaro returns the value of the *last* refresh,
        so we just send two refreshes.
        """
        args = self._request_args
        if args is None:
             args = self._make_request_args()
        async with await session.request(args.method, args.url, **args.kwargs):
            self._last_read_time = time.time()
        return await session.request(args.method, args.url, **args.kwargs)

    async def _convert(self, response: ClientResponse) -> Optional[Message]:
        try:
            voltage = FibaroRefreshResponse(
                **await response.json()
            ).get_voltage()
            if voltage >= self._max_voltage:
                return None
            rt = r_from_v(voltage, self._max_voltage)
            if rt <= 0:
                return None
            temp_c = thermistor_temp_c_beta_formula(rt)
            temp_c1000 = int(temp_c * 1000)
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
