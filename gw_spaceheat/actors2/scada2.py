"""Scada implementation"""

import asyncio
import time
import typing
from typing import (
    Any,
    List,
    Optional,
)
from abc import abstractmethod, ABC

from paho.mqtt.client import MQTTMessageInfo

from actors.scada import ScadaCmdDiagnostic
from actors.utils import QOS
from actors2.actor_interface import ActorInterface
from actors2.message import (
    GtDispatchBooleanLocalMessage,
    ScadaDBG,
    ScadaDBGCommands,
)
from actors2.scada_data import ScadaData
from actors2.scada_interface import ScadaInterface
from config import ScadaSettings
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from proactor.logger import ProactorLogger
from proactor.message import MQTTReceiptPayload, Message
from proactor.proactor_implementation import Proactor, MQTTCodec
from schema.decoders import Decoders
from schema.decoders_factory import DecoderExtractor
from schema.gs.gs_pwr import GsPwr
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean import GtDispatchBoolean
from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean_maker import (
    GtDispatchBoolean_Maker,
)
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local import (
    GtDispatchBooleanLocal,
)
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd import (
    GtDriverBooleanactuatorCmd,
)
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker import GtDriverBooleanactuatorCmd_Maker
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd import GtShCliAtnCmd
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd_maker import GtShCliAtnCmd_Maker
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor import (
    GtShTelemetryFromMultipurposeSensor,
)
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import \
    GtShTelemetryFromMultipurposeSensor_Maker
from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from actors.utils import gw_mqtt_topic_encode, gw_mqtt_topic_decode

class ScadaMQTTCodec(MQTTCodec, ABC):
    ENCODING = "utf-8"
    hardware_layout: HardwareLayout
    decoders: Decoders

    def __init__(self, hardware_layout: HardwareLayout, decoders: Decoders):
        self.hardware_layout = hardware_layout
        self.decoders = Decoders().merge(decoders)
        super().__init__()

    def encode(self, payload: Any) -> bytes:
        if isinstance(payload, bytes):
            encoded = payload
        else:
            payload_as_type = payload.as_type()
            if isinstance(payload_as_type, bytes):
                encoded = payload_as_type
            else:
                encoded = payload_as_type.encode(self.ENCODING)
        return encoded

    def decode(self, receipt_payload: MQTTReceiptPayload) -> Any:
        try:
            decoded_topic = gw_mqtt_topic_decode(receipt_payload.message.topic)
            (from_alias, type_alias) = decoded_topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if type_alias not in self.decoders:
            raise Exception(
                f"Type {type_alias} not recognized. Available decoders: {self.decoders.types()}"
            )
        self.validate_source_alias(from_alias)
        return self.decoders.decode_str(type_alias, receipt_payload.message.payload.decode(self.ENCODING))

    @abstractmethod
    def validate_source_alias(self, source_alias: str):
        pass

class GridworksMQTTCodec(ScadaMQTTCodec):

    def __init__(self, hardware_layout: HardwareLayout):
        super().__init__(
            hardware_layout,
            decoders=DecoderExtractor().from_objects(
                [
                    GtDispatchBoolean_Maker,
                    GtShCliAtnCmd_Maker,
                ]
            )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.atn_g_node_alias:
            raise Exception(
                f"alias {source_alias} not my AtomicTNode ({self.hardware_layout.atn_g_node_alias})!"
            )


class LocalMQTTCodec(ScadaMQTTCodec):

    def __init__(self, hardware_layout: HardwareLayout):
        super().__init__(
            hardware_layout,
            decoders=DecoderExtractor().from_objects(
                [
                    GsPwr_Maker,
                    GtDriverBooleanactuatorCmd_Maker,
                    GtShTelemetryFromMultipurposeSensor_Maker,
                    GtTelemetry_Maker,
                ],
            )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias not in self.hardware_layout.nodes.keys():
            raise Exception(f"alias {source_alias} not in ShNode.by_alias keys!")


class Scada2(ScadaInterface, Proactor):
    GS_PWR_MULTIPLIER = 1
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors2"
    GRIDWORKS_MQTT = "gridworks"
    LOCAL_MQTT = "local"

    _settings: ScadaSettings
    _nodes: HardwareLayout
    _node: ShNode
    _data: ScadaData
    _last_status_second: int
    _scada_atn_fast_dispatch_contract_is_alive_stub: bool

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
        actor_nodes: Optional[List[ShNode]] = None,
    ):
        super().__init__(
            name=name,
            logger=ProactorLogger(**settings.logging.qualified_logger_names())
        )
        self._node = hardware_layout.node(name)
        self._settings = settings
        self._layout = hardware_layout
        self._data = ScadaData(settings, hardware_layout)
        self._add_mqtt_client(
            Scada2.LOCAL_MQTT, self.settings.local_mqtt, LocalMQTTCodec(self._layout)
        )
        self._add_mqtt_client(
            Scada2.GRIDWORKS_MQTT,
            self.settings.gridworks_mqtt,
            GridworksMQTTCodec(self._layout),
        )
        # TODO: take care of subscriptions better. They should be registered here and only subscribed on connect.
        self._mqtt_clients.subscribe(
            Scada2.GRIDWORKS_MQTT,
            gw_mqtt_topic_encode(f"{self._layout.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}"),
            QOS.AtMostOnce,
        )
        self._mqtt_clients.subscribe(
            Scada2.GRIDWORKS_MQTT,
            gw_mqtt_topic_encode(f"{self._layout.atn_g_node_alias}/{GtShCliAtnCmd_Maker.type_alias}"),
            QOS.AtMostOnce,
        )
        # TODO: clean this up
        self.log_subscriptions("construction")
        now = int(time.time())
        self._last_status_second = int(now - (now % self.settings.seconds_per_report))
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
        if actor_nodes is not None:
            for actor_node in actor_nodes:
                self.add_communicator(
                    ActorInterface.load(
                        actor_node.alias,
                        actor_node.actor_class.value,
                        self,
                        self.DEFAULT_ACTORS_MODULE
                    )
                )

    def _start_derived_tasks(self):
        self._tasks.append(
            asyncio.create_task(self.update_status(), name="update_status")
        )

    async def update_status(self):
        while not self._stop_requested:
            if self.time_to_send_status():
                self.send_status()
                self._last_status_second = int(time.time())
            await asyncio.sleep(self.seconds_until_next_status())

    def send_status(self):
        status = self._data.make_status(self._last_status_second)
        self._data.status_to_store[status.StatusUid] = status
        self._publish_to_gridworks(status)
        self._publish_to_local(self._node, status)
        self._publish_to_gridworks(self._data.make_snapshot())
        self._data.flush_latest_readings()

    def next_status_second(self) -> int:
        last_status_second_nominal = int(
            self._last_status_second
            - (self._last_status_second % self.settings.seconds_per_report)
        )
        return last_status_second_nominal + self.settings.seconds_per_report

    def seconds_until_next_status(self) -> float:
        return self.next_status_second() - time.time()

    def time_to_send_status(self) -> bool:
        return time.time() > self.next_status_second()

    @property
    def alias(self):
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    def gridworks_mqtt_topic(self, payload: Any) -> str:
        return gw_mqtt_topic_encode(f"{self._layout.scada_g_node_alias}/{payload.TypeAlias}")

    @classmethod
    def local_mqtt_topic(cls, from_alias: str, payload: Any) -> str:
        return f"{from_alias}/{payload.TypeAlias}"

    def _publish_to_gridworks(
        self, payload, qos: QOS = QOS.AtMostOnce
    ) -> MQTTMessageInfo:
        return self._encode_and_publish(
            Scada2.GRIDWORKS_MQTT,
            topic=self.gridworks_mqtt_topic(payload),
            payload=payload,
            qos=qos,
        )

    def _publish_to_local(self, from_node: ShNode, payload, qos: QOS = QOS.AtMostOnce):
        return self._encode_and_publish(
            Scada2.LOCAL_MQTT,
            topic=self.local_mqtt_topic(from_node.alias, payload),
            payload=payload,
            qos=qos,
        )

    async def _derived_process_message(self, message: Message):
        self._logger.path("++Scada2._derived_process_message %s/%s", message.header.src, message.header.message_type)
        path_dbg = 0
        from_node = self._layout.node(message.header.src, None)
        if isinstance(message.payload, GsPwr):
            path_dbg |= 0x00000001
            if from_node is self._layout.power_meter_node:
                path_dbg |= 0x00000002
                self.gs_pwr_received(message.payload)
            else:
                raise Exception(
                    f"message.header.src {message.header.src} must be from {self._layout.power_meter_node} for GsPwr message"
                )
        elif isinstance(message.payload, GtDispatchBooleanLocal):
            path_dbg |= 0x00000004
            if message.header.src == "a.home":
                path_dbg |= 0x00000008
                await self.local_boolean_dispatch_received(message.payload)
            else:
                raise Exception(
                    "message.header.src must be a.home for GsDispatchBooleanLocal message"
                )
        elif isinstance(message.payload, GtTelemetry):
            path_dbg |= 0x00000010
            if from_node in self._layout.my_simple_sensors:
                path_dbg |= 0x00000020
                self.gt_telemetry_received(from_node, message.payload)
        elif isinstance(message.payload, GtShTelemetryFromMultipurposeSensor):
            path_dbg |= 0x00000040
            if from_node in self._layout.my_multipurpose_sensors:
                path_dbg |= 0x00000080
                self.gt_sh_telemetry_from_multipurpose_sensor_received(
                    from_node, message.payload
                )
        elif isinstance(message.payload, GtDriverBooleanactuatorCmd):
            path_dbg |= 0x00000100
            if from_node in self._layout.my_boolean_actuators:
                path_dbg |= 0x00000200
                self.gt_driver_booleanactuator_cmd_record_received(
                    from_node, message.payload
                )
        elif isinstance(message.payload, ScadaDBG):
            path_dbg |= 0x00000400
            # TODO: mqtt????
            match message.payload.command:
                case ScadaDBGCommands.show_subscriptions:
                    path_dbg |= 0x00000400
                    self.log_subscriptions("message")
        else:
            raise ValueError(
                f"There is not handler for mqtt message payload type [{type(message.payload)}]"
            )
        self._logger.path("--Scada2._derived_process_message  path:0x%08X", path_dbg)

    # TODO: Clean this up
    # noinspection PyProtectedMember
    def log_subscriptions(self, tag=""):
        if self._logger.lifecycle_enabled:
            s = f"Scada2 subscriptions: [{tag}]]\n"
            for client in self._mqtt_clients._clients:
                s += f"\t{client}\n"
                for subscription in self._mqtt_clients._clients[client]._subscriptions:
                    s += f"\t\t[{subscription}]\n"
            self._logger.lifecycle(s)

    async def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path("++Scada2._derived_process_mqtt_message %s", message.payload.message.topic)
        path_dbg = 0
        if message.payload.client_name != self.GRIDWORKS_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.payload.message.topic}]"
            )
        if isinstance(decoded, GtDispatchBoolean):
            path_dbg |= 0x00000001
            await self._boolean_dispatch_received(decoded)
        elif isinstance(decoded, GtShCliAtnCmd):
            path_dbg |= 0x00000002
            self._gt_sh_cli_atn_cmd_received(decoded)
        elif isinstance(decoded, GtTelemetry):
            path_dbg |= 0x00000004
            self._process_telemetry(message, decoded)
        else:
            raise ValueError(
                f"There is not handler for mqtt message payload type [{type(decoded)}]"
                f"Received\n\t topic: [{message.payload.message.topic}]"
            )
        self._logger.path("--Scada2._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _process_telemetry(self, message: Message, decoded: GtTelemetry):
        from_node = self._layout.node(message.header.src)
        if from_node in self._layout.my_simple_sensors:
            self._data.recent_simple_values[from_node].append(decoded.Value)
            self._data.recent_simple_read_times_unix_ms[from_node].append(
                decoded.ScadaReadTimeUnixMs
            )
            self._data.latest_simple_value[from_node] = decoded.Value

    async def _boolean_dispatch_received(
        self, payload: GtDispatchBoolean
    ) -> ScadaCmdDiagnostic:
        """This is a dispatch message received from the atn. It is
        honored whenever DispatchContract with the Atn is live."""
        if not self.scada_atn_fast_dispatch_contract_is_alive:
            return ScadaCmdDiagnostic.IGNORING_ATN_DISPATCH
        return await self._process_boolean_dispatch(payload)

    async def _process_boolean_dispatch(
        self, payload: GtDispatchBoolean
    ) -> ScadaCmdDiagnostic:
        ba = self._layout.node(payload.AboutNodeAlias)
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        await self._communicators[ba.alias].process_message(
            GtDispatchBooleanLocalMessage(
                src=self.name, dst=ba.alias, relay_state=payload.RelayState
            )
        )
        return ScadaCmdDiagnostic.SUCCESS

    def _set_relay_state(self, ba: ShNode, on: bool):
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        self.send_threadsafe(
            GtDispatchBooleanLocalMessage(
                src=self._layout.home_alone_node.alias, dst=ba.alias, relay_state=int(on)
            )
        )
        return ScadaCmdDiagnostic.SUCCESS

    def turn_on(self, ba: ShNode) -> ScadaCmdDiagnostic:
        return self._set_relay_state(ba, True)

    def turn_off(self, ba: ShNode) -> ScadaCmdDiagnostic:
        return self._set_relay_state(ba, False)

    def _gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return
        self._publish_to_gridworks(self._data.make_snapshot())

    @property
    def scada_atn_fast_dispatch_contract_is_alive(self):
        """
        TO IMPLEMENT:

         False if:
           - no contract exists
           - interactive polling between atn and scada is down
           - scada sent dispatch command with more than 6 seconds before response
             as measured by power meter (requires a lot of clarification)
           - average time for response to dispatch commands in last 50 dispatches
             exceeds 3 seconds
           - Scada has not sent in daily attestion that power metering is
             working and accurate
           - Scada requests local control and Atn has agreed
           - Atn requests that Scada take local control and Scada has agreed
           - Scada has not sent in an attestion that metering is good in the
             previous 24 hours

           Otherwise true

           Note that typically, the contract will not be alive because of house to
           cloud comms failure. But not always. There will be significant and important
           times (like when testing home alone perforamance) where we will want to send
           status messages etc up to the cloud even when the dispatch contract is not
           alive.
        """
        return self._scada_atn_fast_dispatch_contract_is_alive_stub

    @property
    def settings(self):
        return self._settings

    @property
    def hardware_layout(self) -> HardwareLayout:
        return self._layout

    def gs_pwr_received(self, payload: GsPwr):
        """The highest priority of the SCADA, from the perspective of the electric grid,
        is to report power changes as quickly as possible (i.e. milliseconds matter) on
        any asynchronous change more than x% (probably 2%).

        There is a single meter measuring all power getting reported - this is in fact
        what is Atomic (i.e. cannot be divided further) about the AtomicTNode. The
        asynchronous change calculation is already made in the power meter code. This
        function just passes through the result.

        The allocation to separate metered nodes is done ex-poste using the multipurpose
        telemetry data."""

        self._publish_to_gridworks(payload, QOS.AtMostOnce)
        self._data.latest_total_power_w = self.GS_PWR_MULTIPLIER * payload.Power

    def gt_sh_telemetry_from_multipurpose_sensor_received(
        self, from_node: ShNode, payload: GtShTelemetryFromMultipurposeSensor
    ):
        if from_node in self._layout.my_multipurpose_sensors:
            about_node_alias_list = payload.AboutNodeAliasList
            for idx, about_alias in enumerate(about_node_alias_list):
                if about_alias not in self._layout.nodes:
                    raise Exception(
                        f"alias {about_alias} in payload.AboutNodeAliasList not a recognized ShNode!"
                    )
                tt = TelemetryTuple(
                    AboutNode=self._layout.node(about_alias),
                    SensorNode=from_node,
                    TelemetryName=payload.TelemetryNameList[idx],
                )
                if tt not in self._layout.my_telemetry_tuples:
                    raise Exception(f"Scada not tracking telemetry tuple {tt}!")
                self._data.recent_values_from_multipurpose_sensor[tt].append(
                    payload.ValueList[idx]
                )
                self._data.recent_read_times_unix_ms_from_multipurpose_sensor[
                    tt
                ].append(payload.ScadaReadTimeUnixMs)
                self._data.latest_value_from_multipurpose_sensor[
                    tt
                ] = payload.ValueList[idx]

    def gt_telemetry_received(self, from_node: ShNode, payload: GtTelemetry):
        self._data.recent_simple_values[from_node].append(payload.Value)
        self._data.recent_simple_read_times_unix_ms[from_node].append(
            payload.ScadaReadTimeUnixMs
        )
        self._data.latest_simple_value[from_node] = payload.Value

    def gt_driver_booleanactuator_cmd_record_received(
        self, from_node: ShNode, payload: GtDriverBooleanactuatorCmd
    ):
        """The boolean actuator actor reports when it has sent an actuation command
        to its driver. We add this to information to be sent up in the 5 minute status
        package.

        This is different than reporting a _reading_ of the state of the
        actuator. Note that a reading of the state of the actuator may not mean the relay
        is in the read position. For example, the NCD relay requires two power sources - one
        from the Pi and one a lowish DC voltage from another plug (12 or 24V). If the second
        power source is off, the relay will still report being on when it is actually off.

        Note also that the thing getting actuated (for example the boost element in the water
        tank) may not be getting any power because of another relay in series. For example, we
        can throw a large 240V breaker in the test garage and the NCD relay will actuate without
        the boost element turning on. Or the element could be burned out.

        So measuring the current and/or power of the thing getting
        actuated is really the best test."""

        if from_node not in self._layout.my_boolean_actuators:
            raise Exception(
                "boolean actuator command records must come from boolean actuator"
            )
        if from_node.alias != payload.ShNodeAlias:
            raise Exception("Command record must come from the boolean actuator actor")
        self._data.recent_ba_cmds[from_node].append(payload.RelayState)
        self._data.recent_ba_cmd_times_unix_ms[from_node].append(
            payload.CommandTimeUnixMs
        )

    async def local_boolean_dispatch_received(
        self, payload: GtDispatchBooleanLocal
    ) -> ScadaCmdDiagnostic:
        """This will be a message from HomeAlone, honored when the DispatchContract
        with the Atn is not live."""
        if self.scada_atn_fast_dispatch_contract_is_alive:
            return ScadaCmdDiagnostic.IGNORING_HOMEALONE_DISPATCH
        return await self._process_boolean_dispatch(
            typing.cast(GtDispatchBoolean, payload)
        )
