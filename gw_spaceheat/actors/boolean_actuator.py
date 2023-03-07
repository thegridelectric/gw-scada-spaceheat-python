"""Implements BooleanActuator via SimpleSensor and SimpleSensorDriverThread."""

from typing import Any
from typing import Optional

from gwproto.messages import GtDispatchBooleanLocal
from pydantic import BaseModel
from result import Err
from result import Ok
from result import Result

from actors.message import GtDriverBooleanactuatorCmdResponse
from actors.scada_interface import ScadaInterface
from actors.simple_sensor import SimpleSensor
from actors.simple_sensor import SimpleSensorDriverThread
from gwproactor.message import Message
from gwproactor.sync_thread import SyncAsyncInteractionThread


class DispatchRelay(BaseModel):
    relay_state: bool


class BooleanActuatorDriverThread(SimpleSensorDriverThread):

    def report_now(self, previous_value: Any) -> bool:
        return previous_value != self._telemetry_value

    def _handle_message(self, message: Any) -> None:
        if isinstance(message, DispatchRelay):
            if message.relay_state:
                self._config.driver.turn_on()
            else:
                self._config.driver.turn_off()
            if int(message.relay_state) != int(self._telemetry_value):
                previous_value = self._telemetry_value
                self.update_telemetry_value()
                if self.report_now(previous_value):
                    self.report_telemetry()


class BooleanActuator(SimpleSensor):
    def __init__(
        self,
        name: str,
        services: ScadaInterface,
        driver_thread: Optional[SyncAsyncInteractionThread] = None,
        responsive_sleep_step_seconds: float = SimpleSensorDriverThread.SLEEP_STEP_SECONDS,
        daemon: bool = True,
    ):
        super().__init__(
            name=name,
            services=services,
            driver_thread=driver_thread,
            driver_thread_class=BooleanActuatorDriverThread,
            driver_receives_messages=True,
            responsive_sleep_step_seconds=responsive_sleep_step_seconds,
            daemon=daemon,
        )

    def _process_dispatch_message(self, message: Message[GtDispatchBooleanLocal]) -> Result[bool, BaseException]:
        self.services.send(
            GtDriverBooleanactuatorCmdResponse(
                src=self.name,
                dst=self.services.name,
                relay_state=message.Payload.RelayState,
            )
        )
        self.send_driver_message(
            DispatchRelay(relay_state=bool(message.Payload.RelayState))
        )
        return Ok()

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, GtDispatchBooleanLocal):
            return self._process_dispatch_message(message)
        return Err(ValueError(f"Error. BooleanActuator {self.name} receieved unexpected message: {message.Header}"))
