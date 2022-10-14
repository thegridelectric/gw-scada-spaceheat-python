"""SimpleSensor implementation.

The SimpleSensor delegates most of its work to a SimpleSensorDriverThread. SimpleSensorDriverThread in turn delegates
its threading infrastructure to SyncAsyncInteractionThread. SimpleSensors provides SimpleSensorDriverThread with an
optionally bi-directional bridge to the rest of the proactor universe.

"""

import asyncio
import queue
import time
from typing import Any
from typing import Optional
from typing import Type

from actors2.actor import SyncThreadActor
from actors2.message import GtTelemetryMessage
from actors2.scada_interface import ScadaInterface
from data_classes.node_config import NodeConfig
from proactor.sync_thread import SyncAsyncInteractionThread
from proactor.sync_thread import SyncAsyncQueueWriter


class SimpleSensorDriverThread(SyncAsyncInteractionThread):
    MAIN_LOOP_MIN_TIME_S = 0.2

    _telemetry_value: Optional[int] = None
    _telemetry_destination: str
    _last_sent_s: float = 0.0
    _config: NodeConfig

    def __init__(
        self,
        name: str,
        config: NodeConfig,
        telemetry_destination: str,
        channel: SyncAsyncQueueWriter,
        responsive_sleep_step_seconds=0.01,
        daemon: Optional[bool] = True,
    ):
        super().__init__(
            channel=channel,
            name=name,
            responsive_sleep_step_seconds=responsive_sleep_step_seconds,
            daemon=daemon,
        )
        self._telemetry_destination = telemetry_destination
        self._config = config

    def _iterate(self) -> None:
        loop_start_s = time.time()
        previous_value = self._telemetry_value
        self.update_telemetry_value()
        if self.report_now(previous_value) or (self.is_time_to_report() and not self.filter(previous_value)):
            self.report_telemetry()
        now_s = time.time()
        if (now_s - loop_start_s) < self.MAIN_LOOP_MIN_TIME_S:
            self._iterate_sleep_seconds = self.MAIN_LOOP_MIN_TIME_S - (
                now_s - loop_start_s
            )
        else:
            self._iterate_sleep_seconds = None

    def report_telemetry(self) -> None:
        """Publish the telemetry value, using exponent and telemetry_name from
        self.config.reporting"""
        if self.running and self._telemetry_value is not None:
            now_seconds = time.time()
            self._put_to_async_queue(
                GtTelemetryMessage(
                    src=self.name,
                    dst=self._telemetry_destination,
                    telemetry_name=self._config.reporting.TelemetryName,
                    value=int(self._telemetry_value),
                    exponent=self._config.reporting.Exponent,
                    scada_read_time_unix_ms=int(now_seconds * 1000),
                )
            )
            self._last_sent_s = int(now_seconds)

    def is_time_to_report(self) -> bool:
        """Returns True if it is time to report, The sensor is supposed to report every
        self.config.reporting.SamplePeriodS seconds - that is, if this number is 5, then
        the report will happen ASAP after top of the hour, then again 5 seconds later, etc ).
        """
        now_s = time.time()
        if int(now_s) == self._last_sent_s:
            return False
        elif now_s - self._last_sent_s >= self._config.reporting.SamplePeriodS:
            return True
        else:
            return False

    def update_telemetry_value(self):
        """Updates self.telemetry_value, using the config.driver"""
        self._telemetry_value = self._config.driver.read_telemetry_value()

    def report_now(self, previous_value: Any) -> bool:
        return False

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def filter(self, previous_value: Any) -> bool:
        return False


class SimpleSensor(SyncThreadActor):

    def __init__(
        self,
        name: str,
        services: ScadaInterface,
        driver_thread: Optional[SyncAsyncInteractionThread] = None,
        driver_thread_class: Optional[Type[SyncAsyncInteractionThread]] = None,
        driver_receives_messages: bool = False,
        responsive_sleep_step_seconds: float = SyncAsyncInteractionThread.SLEEP_STEP_SECONDS,
        daemon: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        if driver_thread is None:
            if driver_thread_class is None:
                driver_thread_class = SimpleSensorDriverThread
            driver_thread = driver_thread_class(
                name=name,
                config=NodeConfig(services.hardware_layout.node(name), services.settings),
                telemetry_destination=services.name,
                channel=SyncAsyncQueueWriter(
                    loop=loop if loop is not None else asyncio.get_event_loop(),
                    async_queue=services.async_receive_queue,
                    sync_queue=queue.Queue() if driver_receives_messages else None,
                ),
                responsive_sleep_step_seconds=responsive_sleep_step_seconds,
                daemon=daemon,
            )
        super().__init__(name, services, driver_thread)

