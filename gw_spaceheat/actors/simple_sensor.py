#  Simple Sensor actor currently on sabbatical
# 
# """SimpleSensor implementation.

# The SimpleSensor delegates most of its work to a SimpleSensorDriverThread. SimpleSensorDriverThread in turn delegates
# its threading infrastructure to SyncAsyncInteractionThread. SimpleSensors provides SimpleSensorDriverThread with an
# optionally bi-directional bridge to the rest of the proactor universe.

# """

# import queue
# import time
# from typing import Any
# from typing import Optional
# from typing import Type

# from gwproto import Message

# from actors.message import GtTelemetryMessage
# from actors.scada_interface import ScadaInterface
# from data_classes.node_config import NodeConfig
# from gwproactor import Problems
# from gwproactor import SyncThreadActor
# from gwproactor.message import InternalShutdownMessage
# from gwproactor.sync_thread import SyncAsyncInteractionThread
# from gwproactor.sync_thread import SyncAsyncQueueWriter


# class SimpleSensorDriverThread(SyncAsyncInteractionThread):
#     MAIN_LOOP_MIN_TIME_S = 0.2

#     _telemetry_value: Optional[int] = None
#     _telemetry_destination: str
#     _last_sent_s: float = 0.0
#     _config: NodeConfig
#     _nominal_sleep_seconds: float = MAIN_LOOP_MIN_TIME_S

#     def __init__(
#         self,
#         name: str,
#         config: NodeConfig,
#         telemetry_destination: str,
#         channel: SyncAsyncQueueWriter,
#         responsive_sleep_step_seconds=0.01,
#         daemon: Optional[bool] = True,
#     ):
#         super().__init__(
#             channel=channel,
#             name=name,
#             responsive_sleep_step_seconds=responsive_sleep_step_seconds,
#             daemon=daemon,
#         )
#         self._telemetry_destination = telemetry_destination
#         self._config = config
#         component_poll_period = getattr(
#             self._config.driver.component,
#             "poll_period_s",
#             None
#         )
#         if component_poll_period is not None and component_poll_period > 0:
#             self._nominal_sleep_seconds = component_poll_period

#     def _report_problems(self, problems: Problems, tag: str):
#         self._put_to_async_queue(
#             Message(
#                 Payload=problems.problem_event(
#                     summary=f"Driver problems: {tag} for {self._config.driver.component}",
#                 )
#             )
#         )

#     def _preiterate(self) -> None:
#         result = self._config.driver.start()
#         if result.is_ok():
#             if result.value.warnings:
#                 self._report_problems(Problems(warnings=result.value.warnings), "startup warning")
#         else:
#             self._report_problems(Problems(errors=[result.err()]), "startup error")
#             self._put_to_async_queue(
#                 InternalShutdownMessage(Src=self.name, Reason=f"Driver start error for {self.name}")
#             )

#     def _iterate(self) -> None:
#         loop_start_s = time.time()
#         previous_value = self._telemetry_value
#         self.update_telemetry_value()
#         if self.report_now(previous_value) or (self.is_time_to_report() and not self.filter(previous_value)):
#             self.report_telemetry()
#         elapsed_s = time.time() - loop_start_s
#         if elapsed_s < self._nominal_sleep_seconds:
#             self._iterate_sleep_seconds = self._nominal_sleep_seconds - elapsed_s
#         else:
#             self._iterate_sleep_seconds = None

#     def report_telemetry(self) -> None:
#         """Publish the telemetry value, using exponent and telemetry_name from
#         self.config.reporting"""
#         if self.running and self._telemetry_value is not None:
#             now_seconds = time.time()
#             self._put_to_async_queue(
#                 GtTelemetryMessage(
#                     src=self.name,
#                     dst=self._telemetry_destination,
#                     telemetry_name=self._config.reporting.TelemetryName,
#                     value=int(self._telemetry_value),
#                     exponent=self._config.reporting.Exponent,
#                     scada_read_time_unix_ms=int(now_seconds * 1000),
#                 )
#             )
#             self._last_sent_s = int(now_seconds)

#     def is_time_to_report(self) -> bool:
#         """Returns True if it is time to report, The sensor is supposed to report every
#         self.config.reporting.SamplePeriodS seconds - that is, if this number is 5, then
#         the report will happen ASAP after top of the hour, then again 5 seconds later, etc ).
#         """
#         now_s = time.time()
#         if int(now_s) == self._last_sent_s:
#             return False
#         elif now_s - self._last_sent_s >= self._config.reporting.SamplePeriodS:
#             return True
#         else:
#             return False

#     def update_telemetry_value(self):
#         """Updates self.telemetry_value, using the config.driver"""
#         read = self._config.driver.read_telemetry_value()
#         if read.is_ok():
#             if read.value.value is not None:
#                 self._telemetry_value = read.value.value
#             if read.value.warnings:
#                 self._report_problems(Problems(warnings=read.value.warnings), "read warnings")

#     def report_now(self, previous_value: Any) -> bool:
#         return False

#     # noinspection PyMethodMayBeStatic,PyUnusedLocal
#     def filter(self, previous_value: Any) -> bool:
#         return False


# class SimpleSensor(SyncThreadActor):

#     def __init__(
#         self,
#         name: str,
#         services: ScadaInterface,
#         driver_thread: Optional[SyncAsyncInteractionThread] = None,
#         driver_thread_class: Optional[Type[SyncAsyncInteractionThread]] = None,
#         driver_receives_messages: bool = False,
#         responsive_sleep_step_seconds: float = SyncAsyncInteractionThread.SLEEP_STEP_SECONDS,
#         daemon: bool = True,
#     ):
#         if driver_thread is None:
#             if driver_thread_class is None:
#                 driver_thread_class = SimpleSensorDriverThread
#             driver_thread = driver_thread_class(
#                 name=name,
#                 config=NodeConfig(services.hardware_layout.node(name), services.settings),
#                 telemetry_destination=services.name,
#                 channel=SyncAsyncQueueWriter(queue.Queue() if driver_receives_messages else None),
#                 responsive_sleep_step_seconds=responsive_sleep_step_seconds,
#                 daemon=daemon,
#             )
#         super().__init__(name, services, driver_thread)
