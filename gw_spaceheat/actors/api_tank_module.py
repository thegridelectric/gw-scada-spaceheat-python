import json
import math
from functools import cached_property
from typing import Callable
from typing import Dict, List
from typing import Literal
from typing import Optional
from typing import Sequence
import re
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from gwproactor import Actor
from gwproactor import Problems
from gwproactor import ServicesInterface
from gwproto import Message
from gwproto.types import ComponentGt
from gwproto.data_classes.components import Component
from gwproto.types import ComponentAttributeClassGt
from gwproto.types.web_server_gt import DEFAULT_WEB_SERVER_NAME
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator, model_validator
from result import Ok
from result import Result
from actors.message import SyncedReadingsMessage
from typing_extensions import Self

R_FIXED_KOHMS = 5.65
R_PICO_KOHMS = 30
THERMISTOR_BETA = 3977
THERMISTOR_T0 = 298  # i.e. 25 degrees C
THERMISTOR_R0_KOHMS = 10

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


class PicoTankModuleComponentGt(ComponentGt):
    PicoHwUidList: List[str]
    Enabled: bool
    SendMicroVolts: bool
    Samples: int
    NumSampleAverages: int
    TypeName: Literal["pico.tank.module.component.gt"] = "pico.tank.module.component.gt"
    Version: Literal["000"] = "000"

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        if len(self.PicoHwUidList) != 2:
            raise ValueError("Check Axiom 1: Tank Modules have two picos!")
        if len(self.ConfigList) != 4:
            raise ValueError("Check Axiom 1: tank modules have 4 configs")
        channel_names = [cfg.ChannelName for cfg in self.ConfigList]
        actor_names = {n.split("-")[0] for n in channel_names}
        if len(actor_names) > 1:
            raise ValueError(f"Channel names need to have the pattern actor_name-depthi")
        for n in channel_names:
            try:
                n.split("-")[1]
            except IndexError as e:
                raise ValueError("Channel names have the pattern actor_name-depthi")
            if not re.match(r"depth[1-4]$", n.split("-")[1]):
                raise ValueError("Channel names have the pattern actor_name-depthi")
            return self
            
    
    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        # TODO: make sure PollPeriod, CapturePeriod, AsyncCapture etc all match between 0/1
        # and 2/3
        return self
        
    

class PicoTankModuleComponent(Component[PicoTankModuleComponentGt, ComponentAttributeClassGt]):
    ...

    

class MicroVolts(BaseModel):
    HwUid: str
    AboutNodeNameList: List[str]
    MicroVoltsList: List[int]
    TypeName: Literal["microvolts"] = "microvolts"
    Version: Literal["100"] = "100"



class ApiTankModule(Actor):

    _component: PicoTankModuleComponent
    params_by_hw_uid: Dict[str, TankModuleParams]
    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        super().__init__(name, services)
        component = services.hardware_layout.component(name)
        if not isinstance(component, PicoTankModuleComponent):
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
        if self._component.gt.Enabled:
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
        self.params_by_hw_uid = {}
        self.set_params()
        
    def set_params(self) -> None:
        c = self._component.gt
        id_a = c.PicoHwUidList[0]
        self.params_by_hw_uid[id_a] = TankModuleParams(
            HwUid=id_a,
            ActorNodeName=self.name,
            PicoAB="a",
            CapturePeriodS=c.ConfigList[0].CapturePeriodS,
            Samples=c.Samples,
            NumSampleAverages=c.NumSampleAverages,
            AsyncCaptureDeltaMicroVolts=c.ConfigList[0].AsyncCaptureDelta, 
        )
        id_b = c.PicoHwUidList[1]
        self.params_by_hw_uid[id_b] = TankModuleParams(
            HwUid=id_a,
            ActorNodeName=self.name,
            PicoAB="b",
            CapturePeriodS=c.ConfigList[2].CapturePeriodS,
            Samples=c.Samples,
            NumSampleAverages=c.NumSampleAverages,
            AsyncCaptureDeltaMicroVolts=c.ConfigList[2].AsyncCaptureDelta, 
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

    def _process_microvolts(self, data: MicroVolts) -> None:
        about_node_list = []
        value_list = []
        for i in range(len(data.AboutNodeNameList)):
            volts = data.MicroVoltsList[i] / 1e6
            try:
                r_therm_kohms = thermistor_resistance(volts)
                temp_c = temp_beta(r_therm_kohms, fahrenheit=False)
                value_list.append(temp_c * 1000)
                about_node_list.append(data.AboutNodeNameList[i])
            except:
                print("note the problem")

        self._send(
                SyncedReadingsMessage(
                    src=self.name,
                    dst=self.services.name,
                    channel_name_list=about_node_list,
                    value_list=value_list,
                )
            )


    def _process_params(self, params: TankModuleParams) -> None:
        if params.HwUid not in self._component.gt.PicoHwUidList:
            return
        else:
            correct_params = self.params_by_hw_uid[params.HwUid]
            # Possibly add error checking. For example
            # if the actor node name is incorrect?
            # TODO: return correct params to the post.
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

def thermistor_resistance(volts, r_fixed=R_FIXED_KOHMS, r_pico=R_PICO_KOHMS):
    r_therm = 1/((3.3/volts-1)/r_fixed - 1/r_pico)
    return r_therm

def temp_beta(r_therm_kohms: float, fahrenheit: bool=False) -> float:
    """
    beta formula specs for the Amphenol MA100GG103BN
    Uses T0 and R0 are a matching pair of values: this is a 10 K thermistor
    which means at 25 deg C (T0) it has a resistance of 10K Ohms
    
    [More info](https://drive.google.com/drive/u/0/folders/1f8SaqCHOFt8iJNW64A_kNIBGijrJDlsx)
    """
    t0, r0, beta = THERMISTOR_T0, THERMISTOR_R0_KOHMS, THERMISTOR_BETA
    r_therm = r_therm_kohms
    temp_c = 1 / ((1/t0) + (math.log(r_therm/r0) / beta)) - 273
    temp_f = 32 + (temp_c * 9/5)
    return round(temp_f, 2) if fahrenheit else round(temp_c, 2)