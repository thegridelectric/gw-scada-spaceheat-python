"""Implements BooleanActuator via SimpleSensor and SimpleSensorDriverThread."""

from typing import Optional, Any

from pydantic import BaseModel

from actors2.message import GtDriverBooleanactuatorCmdResponse
from actors2.simple_sensor import SimpleSensor, SimpleSensorDriverThread
from actors2.scada_interface import ScadaInterface
from proactor.message import Message
from proactor.sync_thread import SyncAsyncInteractionThread
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import (
    GtDispatchBooleanLocal,
)


class DispatchRelay(BaseModel):
    relay_state: bool


class BooleanActuatorDriverThread(SimpleSensorDriverThread):

    def report_now(self, previous_value: Any) -> bool:
        return previous_value != self._telemetry_value

    def update_telemetry_value(self):
        self._telemetry_value = self._config.driver.is_on()

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

    def _process_dispatch_message(self, message: Message[GtDispatchBooleanLocal]):
        self.services.send(
            GtDriverBooleanactuatorCmdResponse(
                src=self.name,
                dst=self.services.name,
                relay_state=message.payload.RelayState,
            )
        )
        self.send_driver_message(
            DispatchRelay(relay_state=bool(message.payload.RelayState))
        )

    async def process_message(self, message: Message):
        if isinstance(message.payload, GtDispatchBooleanLocal):
            self._process_dispatch_message(message)
        else:
            ValueError(
                f"Error. BooleanActuator {self.name} receieved unexpected message: {message.header}"
            )
