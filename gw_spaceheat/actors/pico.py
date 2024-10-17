import json
from functools import cached_property
from typing import Callable
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence

from aiohttp.web_request import Request
from aiohttp.web_response import Response
from gwproactor import Actor
from gwproactor import Problems
from gwproactor import ServicesInterface
from gwproactor.message import MessageType
from gwproto import Message
from gwproto.data_classes.components import Component
from gwproto.data_classes.components.hubitat_component import HubitatComponent
from gwproto.types import ComponentAttributeClassGt
from gwproto.types.web_server_gt import DEFAULT_WEB_SERVER_NAME
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator
from result import Ok
from result import Result

from actors.hubitat_interface import HubitatEventContent
from actors.hubitat_interface import HubitatWebEventHandler
from actors.hubitat_interface import HubitatWebEventListenerInterface
from actors.hubitat_interface import HubitatWebServerInterface
from actors.message import SyncedReadingsMessage


class PicoGt(BaseModel):
    Enabled: bool = True
    HwUid: str
    StuffFromPico: int
    model_config = ConfigDict(extra="allow")

class PiocComponentGt(PicoGt):
    Pico: PicoGt
    TypeName: Literal["pico.component.gt"] = "pico.component.gt"
    Version: Literal["000"] = "000"

class PicoComponent(Component[PiocComponentGt, ComponentAttributeClassGt]):
    ...

class MicroVolts(BaseModel):
    HwUid: str
    AboutNodeNameList: List[str]
    MicroVoltsList: List[int]
    TypeName: Literal["microvolts"] = "microvolts"
    Version: Literal["100"] = "100"

class TankModuleParams(BaseModel):
    HwUid: str
    ActorNodeName: Optional[str]
    PicoAB: Optional[str]
    CapturePeriodS: int
    Samples: int
    NumSampleAverages: int
    AsyncCaptureDeltaMicroVolts: int
    CaptureOffsetS: Optional[float] = 0.0
    TypeName: Literal["tank.module.params"]
    Version: Literal["100"] = "100"

    @field_validator("PicoAB")
    @classmethod
    def _check_pico_a_b(cls, v: str) -> str:
        if v:
            if v not in {"a", "b"}:
                raise ValueError(f"If it exists, PicoAB must be lowercase a or lowercase b, not <{v}>")
        return v


class Pico(Actor):

    _component: PicoComponent

    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        super().__init__(name, services)
        component = services.hardware_layout.component(name)
        if not isinstance(component, PicoComponent):
            display_name = getattr(
                component, "display_name", "MISSING ATTRIBUTE display_name"
            )
            raise ValueError(
                f"ERROR. Component <{display_name}> has type {type(component)}. "
                f"Expected PicoComponent.\n"
                f"  Node: {self.name}\n"
                f"  Component id: {component.gt.ComponentId}"
            )
        self._component = component
        if self._component.gt.Pico.Enabled:
            self._services.add_web_route(
                server_name=DEFAULT_WEB_SERVER_NAME,
                method="POST",
                path="/" + self.microvolts_path,
                handler=self._handle_microvolts_post,
            )
            self._services.add_web_route(
                server_name=DEFAULT_WEB_SERVER_NAME,
                method="POST",
                path="/" + self.params_path,
                handler=self._handle_params_post,
            )

    @cached_property
    def microvolts_path(self) -> str:
        return f"{self.name}/microvolts"

    @cached_property
    def params_path(self) -> str:
        return f"{self.name}/tank-module-params"

    async def _get_text(self, request: Request) -> Optional[str]:
        try:
            return await request.text()
        except Exception as e:
            self.services.send_threadsafe(
                Message(
                    Payload=Problems(errors=[e]).problem_event(
                        summary=(
                            f"ERROR awaiting post ext <{self.name}>: {type(e)} <{e}>"
                        ),
                    )
                )
            )
        return None

    def _report_post_error(self, exception: BaseException, text: str) -> None:
        self.services.send_threadsafe(
            Message(
                Payload=Problems(
                    msg=f"request: <{text}>",
                    errors=[exception]
                ).problem_event(
                    summary=(
                        "Pico POST processing error for "
                        f"<{self._name}>: {type(exception)} <{exception}>"
                    ),
                )
            )
        )

    async def _handle_microvolts_post(self, request: Request) -> Response:
        text = self._get_text(request)
        if isinstance(text, str):
            try:
                self.services.send_threadsafe(
                    Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=MicroVolts(
                            **json.loads(text).get("content", {})
                        )
                    )
                )
            except Exception as e: # noqa
                self._report_post_error(e, text)
        return Response()

    async def _handle_params_post(self, request: Request) -> Response:
        text = self._get_text(request)
        if isinstance(text, str):
            try:
                self.services.send_threadsafe(
                    Message(
                        Src=self.name,
                        Dst=self.name,
                        Payload=TankModuleParams(
                            **json.loads(text).get("content", {})
                        )
                    )
                )
            except Exception as e: # noqa
                self._report_post_error(e, text)
        return Response()

    def _process_microvolts(self, microvolts: MicroVolts) -> None:
        ## filter and optionally send data to scada
        forward_on = False
        if forward_on:
            self._send(
                SyncedReadingsMessage(
                    src=self.name,
                    dst=self.services.name,
                    channel_name_list=[self._component.gt.channel_name],
                    value_list=[-1],
                )
            )

        ...

    def _process_params(self, microvolts: TankModuleParams) -> None:
        ## filter and optionally send data to scada
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case MicroVolts():
                self._process_microvolts(message.Payload)
            case TankModuleParams():
                self._process_params(message.Payload)
        return Ok(True)

    def start(self) -> None:
        """IOLoop will take care of start."""

    def stop(self) -> None:
        """IOLoop will take care of stop."""

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
