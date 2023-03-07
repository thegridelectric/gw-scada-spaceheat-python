"""MQTT infrastructure providing support for multiple MTQTT clients

TODO: Replace synchronous use of Paho MQTT Client with asyncio usage, per Paho documentation or external library

Main current limitation: each interaction between asyncio code and the mqtt clients must either have thread locking
(as is provided inside paho for certain functions such as publish()) or an explicit message based API.

"""
import asyncio
import enum
import logging
import threading
import uuid
from typing import cast
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from paho.mqtt.client import MQTT_ERR_SUCCESS
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessageInfo

from problems import Problems
from proactor import config
from proactor.message import MQTTConnectFailMessage
from proactor.message import MQTTConnectMessage
from proactor.message import MQTTDisconnectMessage
from proactor.message import MQTTProblemsMessage
from proactor.message import MQTTReceiptMessage
from proactor.message import MQTTSubackMessage
from proactor.message import MQTTSubackPayload
from proactor.sync_thread import AsyncQueueWriter
from proactor.sync_thread import responsive_sleep

class QOS(enum.IntEnum):
    AtMostOnce = 0
    AtLeastOnce = 1
    ExactlyOnce = 2

class Subscription(NamedTuple):
    Topic: str
    Qos: QOS


class MQTTClientWrapper:
    _name: str
    _client_config: config.MQTTClient
    _client: PahoMQTTClient
    _stop_requested: bool
    _receive_queue: AsyncQueueWriter
    _subscriptions: Dict[str, int]
    _pending_subscriptions: Set[str]
    _pending_subacks: Dict[int, List[str]]

    def __init__(
        self,
        name: str,
        client_config: config.MQTTClient,
        receive_queue: AsyncQueueWriter,
    ):
        self.name = name
        self._client_config = client_config
        self._receive_queue = receive_queue
        self._client = PahoMQTTClient("-".join(str(uuid.uuid4()).split("-")[:-1]))
        self._client.username_pw_set(
            username=self._client_config.username,
            password=self._client_config.password.get_secret_value(),
        )
        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect
        self._client.on_connect_fail = self.on_connect_fail
        self._client.on_disconnect = self.on_disconnect
        self._client.on_subscribe = self.on_subscribe
        self._subscriptions = dict()
        self._pending_subscriptions = set()
        self._pending_subacks = dict()
        self._thread = threading.Thread(target=self._client_thread, name=f"MQTT-client-thread-{self.name}")
        self._stop_requested = False

    def _client_thread(self):
        MAX_BACK_OFF = 1024
        backoff = 1
        while not self._stop_requested:
            try:
                self._client.connect(self._client_config.host, port=self._client_config.port)
                self._client.loop_forever(retry_first_connection=True)
            except BaseException as e:
                self._receive_queue.put(
                    MQTTProblemsMessage(
                        client_name=self.name,
                        problems=Problems(errors=[e])
                    )
                )
            finally:
                # noinspection PyBroadException
                try:
                    self._client.disconnect()
                except:
                    pass
            if not self._stop_requested:
                if backoff >= MAX_BACK_OFF:
                    backoff = 1
                else:
                    backoff = min(backoff * 2, MAX_BACK_OFF)
                responsive_sleep(self, backoff, running_field_name="_stop_requested", running_field=False)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_requested = True
        self._client.disconnect()
        self._thread.join()

    def publish(self, topic: str, payload: bytes, qos: int) -> MQTTMessageInfo:
        return self._client.publish(topic, payload, qos)

    def subscribe(self, topic: str, qos: int) -> Tuple[int, Optional[int]]:
        self._subscriptions[topic] = qos
        self._pending_subscriptions.add(topic)
        subscribe_result = self._client.subscribe(topic, qos)
        if subscribe_result[0] == MQTT_ERR_SUCCESS:
            self._pending_subacks[subscribe_result[1]] = [topic]
        return subscribe_result

    def subscribe_all(self) -> Tuple[int, Optional[int]]:
        if self._subscriptions:
            topics = list(self._subscriptions.keys())
            for topic in topics:
                self._pending_subscriptions.add(topic)
            subscribe_result = self._client.subscribe(
                list(self._subscriptions.items()), 0
            )
            if subscribe_result[0] == MQTT_ERR_SUCCESS:
                self._pending_subacks[subscribe_result[1]] = topics
        else:
            subscribe_result = MQTT_ERR_SUCCESS, None
        return subscribe_result

    def unsubscribe(self, topic: str) -> Tuple[int, Optional[int]]:
        self._subscriptions.pop(topic, None)
        return self._client.unsubscribe(topic)

    def connected(self) -> bool:
        return self._client.is_connected()

    def num_subscriptions(self) -> int:
        return len(self._subscriptions)

    def num_pending_subscriptions(self) -> int:
        return len(self._pending_subscriptions)

    def subscribed(self) -> bool:
        return self.connected() and (
            not self.num_subscriptions() or not self.num_pending_subscriptions()
        )

    def subscription_items(self) -> list[Tuple[str, int]]:
        return list(cast(list[Tuple[str, int]], self._subscriptions.items()))

    def on_message(self, _, userdata, message):
        self._receive_queue.put(
            MQTTReceiptMessage(
                client_name=self.name,
                userdata=userdata,
                message=message,
            )
        )

    def handle_suback(self, suback: MQTTSubackPayload) -> int:
        topics = self._pending_subacks.pop(suback.mid, [])
        if topics:
            for topic in topics:
                self._pending_subscriptions.remove(topic)
        return len(self._pending_subscriptions)

    def on_subscribe(self, _, userdata, mid, granted_qos):
        self._receive_queue.put(
            MQTTSubackMessage(
                client_name=self.name,
                userdata=userdata,
                mid=mid,
                granted_qos=granted_qos,
            )
        )

    def on_connect(self, _, userdata, flags, rc):
        self._receive_queue.put(
            MQTTConnectMessage(
                client_name=self.name,
                userdata=userdata,
                flags=flags,
                rc=rc,
            )
        )

    def on_connect_fail(self, _, userdata):
        self._receive_queue.put(
            MQTTConnectFailMessage(
                client_name=self.name,
                userdata=userdata,
            )
        )

    def on_disconnect(self, _, userdata, rc):
        self._pending_subscriptions = set(self._subscriptions.keys())
        self._receive_queue.put(
            MQTTDisconnectMessage(
                client_name=self.name,
                userdata=userdata,
                rc=rc,
            )
        )

    def enable_logger(self, logger: Optional[Union[logging.Logger, logging.LoggerAdapter]] = None):
        self._client.enable_logger(logger)

    def disable_logger(self):
        self._client.disable_logger()


class MQTTClients:
    clients: Dict[str, MQTTClientWrapper]
    _send_queue: AsyncQueueWriter
    upstream_client: str = ""
    primary_peer_client: str = ""

    def __init__(self):
        self._send_queue = AsyncQueueWriter()
        self.clients = dict()

    def add_client(
        self,
        name: str,
        client_config: config.MQTTClient,
        upstream: bool = False,
        primary_peer: bool = False,
    ):
        if name in self.clients:
            raise ValueError(f"ERROR. MQTT client named {name} already exists")
        if upstream:
            if self.upstream_client:
                raise ValueError(
                    f"ERROR. upstream client already set as {self.upstream_client}. Client {name} may not be set as upstream.")
            self.upstream_client = name
        if primary_peer:
            if self.primary_peer_client:
                raise ValueError(
                    f"ERROR. primary peer client already set as {self.primary_peer_client}. Client {name} may not be set as primary peer."
                )
            self.primary_peer_client = name
        self.clients[name] = MQTTClientWrapper(name, client_config, self._send_queue)

    def publish(
        self, client: str, topic: str, payload: bytes, qos: int
    ) -> MQTTMessageInfo:
        return self.clients[client].publish(topic, payload, qos)

    def subscribe(self, client: str, topic: str, qos: int) -> Tuple[int, Optional[int]]:
        return self.clients[client].subscribe(topic, qos)

    def subscribe_all(self, client: str) -> Tuple[int, Optional[int]]:
        return self.clients[client].subscribe_all()

    def unsubscribe(self, client: str, topic: str) -> Tuple[int, Optional[int]]:
        return self.clients[client].unsubscribe(topic)

    def handle_suback(self, suback: MQTTSubackPayload) -> int:
        return self.clients[suback.client_name].handle_suback(suback)

    def stop(self):
        for client in self.clients.values():
            client.stop()

    def start(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue):
        self._send_queue.set_async_loop(loop, async_queue)
        for client in self.clients.values():
            client.start()

    def connected(self, client: str) -> bool:
        return self.clients[client].connected()

    def num_subscriptions(self, client: str) -> int:
        return self.clients[client].num_subscriptions()

    def num_pending_subscriptions(self, client: str) -> int:
        return self.clients[client].num_pending_subscriptions()

    def subscribed(self, client: str) -> bool:
        return self.clients[client].subscribed()

    def enable_loggers(self, logger: Optional[Union[logging.Logger, logging.LoggerAdapter]] = None):
        for client_name in self.clients:
            self.clients[client_name].enable_logger(logger)

    def disable_loggers(self):
        for client_name in self.clients:
            self.clients[client_name].disable_logger()

    def client_wrapper(self, client: str) -> MQTTClientWrapper:
        return self.clients[client]

    def upstream(self) -> MQTTClientWrapper:
        return self.clients[self.upstream_client]

    def primary_peer(self) -> MQTTClientWrapper:
        return self.clients[self.primary_peer_client]
