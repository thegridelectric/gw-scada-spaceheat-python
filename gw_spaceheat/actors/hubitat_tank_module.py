import time
from typing import Optional

from aiohttp import ClientResponse
from aiohttp import ClientSession
from gwproactor import Actor
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

class FibaroTankTempPoller(RESTPoller):

    _last_read_time: float
    _report_src: str
    _report_dst: str
    _settings: FibaroTempSensorSettings

    def __init__(
            self,
            name: str,
            tank_module_name: str,
            settings: FibaroTempSensorSettings,
            services: ServicesInterface
    ):
        self._report_src = tank_module_name
        self._report_dst = services.name
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
        return MultipurposeSensorTelemetryMessage(
            src=self._report_src,
            dst=self._report_dst,
            about_node_alias_list=[self._settings.node_name],
            value_list=[
                int(
                    FibaroRefreshResponse(
                        **await response.json()
                    ).get_voltage() * 1000
                )
            ],
            telemetry_name_list=[self._settings.telemetry_name],
        )

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
