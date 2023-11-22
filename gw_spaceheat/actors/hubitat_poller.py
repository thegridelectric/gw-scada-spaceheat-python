import time
from typing import Optional

from aiohttp import ClientResponse
from aiohttp import ClientSession
from gwproactor import Actor
from gwproactor import Problems
from gwproactor import ServicesInterface
from gwproactor.actors.rest import RESTPoller
from gwproto import Message
from gwproto.data_classes.components.hubitat_poller_component import HubitatPollerComponent
from gwproto.types import MakerAPIAttributeGt
from pydantic import BaseModel
from pydantic import Extra
from result import Err
from result import Ok
from result import Result

from actors.message import MultipurposeSensorTelemetryMessage
from drivers.exceptions import DriverWarning


class HubitatAttributeWarning(DriverWarning):
    """An expected attribute was missing from a Hubitat refresh response"""

    node_name: str
    attribute_name: str

    def __init__(
            self,
            node_name: str,
            attribute_name: str,
            msg: str = "",
    ):
        super().__init__(msg)
        self.node_name = node_name
        self.attribute_name = attribute_name

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += (
            f" Attribute: <{self.attribute_name}> "
            f" Node: <{self.node_name}>"
        )
        return s

class HubitatAttributeMissing(HubitatAttributeWarning):
    """An expected attribute was missing from a Hubitat refresh response"""

    def __str__(self):
        return "Missing Attribute  " + super().__str__()

class HubitatAttributeConvertFailure(HubitatAttributeWarning):
    """An expected attribute was missing from a Hubitat refresh response"""

    received: Optional[str | int | float]

    def __init__(
            self,
            node_name: str,
            attribute_name: str,
            received: Optional[str | int | float],
            msg: str = "",
    ):
        super().__init__(
            node_name=node_name,
            attribute_name=attribute_name,
            msg=msg
        )
        self.received = received

    def __str__(self):
        return "Convert failure Attribute  received: {}" + super().__str__()


class MakerAPIAttribute(BaseModel, extra=Extra.allow):
    name: str = ""
    currentValue: Optional[str | int | float] = None
    dataType: str = ""

class MakerAPIRefreshResponse(BaseModel, extra=Extra.allow):
    id: int
    name: str = ""
    label: str = ""
    type: str = ""
    attributes: list[MakerAPIAttribute]

    def get_attribute_by_name(self, name: str) -> Optional[MakerAPIAttribute]:
        return next((attr for attr in self.attributes if attr.name == name), None)


class HubitatRESTPoller(RESTPoller):

    _last_read_time: float
    _report_dst: str
    _component: HubitatPollerComponent

    def __init__(
            self,
            name: str,
            component: HubitatPollerComponent,
            services: ServicesInterface
    ):
        self._report_dst = services.name
        self._component = component
        super().__init__(
            name,
            self._component.rest,
            services.io_loop_manager,
            convert=self._converter,
            forward=services.send_threadsafe,
        )

    async def _make_request(self, session: ClientSession) -> Optional[ClientResponse]:
        """"We assume a refresh sent to hubitat returns the value of the *last* refresh,
        so we just send two refreshes.
        """
        response = await super()._make_request(session)
        if response is None:
            return None
        else:
            async with response:
                self._last_read_time = time.time()
            return await super()._make_request(session)

    @classmethod
    def _convert_attribute(
        cls,
        config_attribute: MakerAPIAttributeGt,
        response: MakerAPIRefreshResponse,
    ) -> Result[Optional[int], BaseException]:
        if config_attribute.enabled:
            response_attribute = response.get_attribute_by_name(
                config_attribute.attribute_name
            )
            if response_attribute is None:
                if config_attribute.report_missing:
                    return Err(HubitatAttributeMissing(
                        config_attribute.node_name,
                        config_attribute.attribute_name
                    ))
            try:
                return Ok(
                    int(
                        float(response_attribute.currentValue)**
                        config_attribute.exponent
                    )
                )
            except BaseException as e:
                return Err(HubitatAttributeConvertFailure(
                    config_attribute.node_name,
                    config_attribute.attribute_name,
                    response_attribute.currentValue,
                    str(e)
                ))
        return Ok(None)

    async def _converter(self, response: ClientResponse) -> Optional[Message]:
        try:
            response = MakerAPIRefreshResponse(
                **await response.json(content_type=None)
            )
            about_nodes = []
            values = []
            telemetry_names = []
            warnings = []
            for config_attribute in self._component.poller_gt.attributes:
                convert_result = self._convert_attribute(
                    config_attribute, response
                )
                if convert_result.ok():
                    about_nodes.append(config_attribute.node_name)
                    values.append(convert_result.value)
                    telemetry_names.append(config_attribute.telemetry_name)
                else:
                    warnings.append(convert_result.err())
            if values:
                return MultipurposeSensorTelemetryMessage(
                    src=self._name,
                    dst=self._report_dst,
                    about_node_alias_list=about_nodes,
                    value_list=values,
                    telemetry_name_list=telemetry_names,
                )
            if warnings:
                self._forward(
                    Message(
                        Payload=Problems(warnings=warnings).problem_event(
                            summary=(
                                f"<{self._name}> _convert() warnings "
                            ), src=self._name
                        )
                    )
                )
        except BaseException as e:
            self._forward(
                Message(
                    Payload=Problems(errors=[e]).problem_event(
                        summary=(
                            f"<{self._name}> _convert() error"
                        ), src=self._name
                    )
                )
            )
        return None

class HubitatPoller(Actor):

    _component: HubitatPollerComponent
    _poller: HubitatRESTPoller

    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        component = services.hardware_layout.component(name)
        if not isinstance(component, HubitatPollerComponent):
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
        self._poller = HubitatRESTPoller(
                name=name,
                component=component,
                services=services,
            )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        raise ValueError("HubitatTankModule does not currently process any messages")

    def start(self) -> None:
        self._poller.start()

    def stop(self) -> None:
        try:
            self._poller.stop()
        except: # noqa
            pass

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
