"""MQTT infrastructure providing support for multiple MTQTT clients

TODO: Replace synchronous use of Paho MQTT Client with asyncio usage, per Paho documentation or external library

Main current limitation: each interaction between asyncio code and the mqtt clients must either have thread locking
(as is provided inside paho for certain functions such as publish()) or an explicit message based API.

"""
import asyncio
import logging
import uuid
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from paho.mqtt.client import MQTT_ERR_SUCCESS
from paho.mqtt.client import Client as PahoMQTTClient
from paho.mqtt.client import MQTTMessageInfo

import config
from proactor.message import MQTTConnectFailMessage
from proactor.message import MQTTConnectMessage
from proactor.message import MQTTDisconnectMessage
from proactor.message import MQTTReceiptMessage
from proactor.message import MQTTSubackMessage
from proactor.message import MQTTSubackPayload
from proactor.sync_thread import AsyncQueueWriter


class MQTTClientWrapper:
    _name: str
    _client_config: config.MQTTClient
    _client: PahoMQTTClient
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

    def start(self):
        self._client.connect(self._client_config.host, port=self._client_config.port)
        self._client.loop_start()

    def stop(self):
        self._client.disconnect()
        self._client.loop_stop()

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
    _clients: Dict[str, MQTTClientWrapper]
    _send_queue: AsyncQueueWriter

    def __init__(self):
        self._send_queue = AsyncQueueWriter()
        self._clients = dict()

    def add_client(
        self,
        name: str,
        client_config: config.MQTTClient,
    ):
        if name in self._clients:
            raise ValueError(f"ERROR. MQTT client named {name} already exists")
        self._clients[name] = MQTTClientWrapper(name, client_config, self._send_queue)

    def publish(
        self, client: str, topic: str, payload: bytes, qos: int
    ) -> MQTTMessageInfo:
        return self._clients[client].publish(topic, payload, qos)

    def subscribe(self, client: str, topic: str, qos: int) -> Tuple[int, Optional[int]]:
        return self._clients[client].subscribe(topic, qos)

    def subscribe_all(self, client: str) -> Tuple[int, Optional[int]]:
        return self._clients[client].subscribe_all()

    def unsubscribe(self, client: str, topic: str) -> Tuple[int, Optional[int]]:
        return self._clients[client].unsubscribe(topic)

    def handle_suback(self, suback: MQTTSubackPayload) -> int:
        return self._clients[suback.client_name].handle_suback(suback)

    def stop(self):
        for client in self._clients.values():
            client.stop()

    def start(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue):
        self._send_queue.set_async_loop(loop, async_queue)
        for client in self._clients.values():
            client.start()

    def connected(self, client: str) -> bool:
        return self._clients[client].connected()

    def num_subscriptions(self, client: str) -> int:
        return self._clients[client].num_subscriptions()

    def num_pending_subscriptions(self, client: str) -> int:
        return self._clients[client].num_pending_subscriptions()

    def subscribed(self, client: str) -> bool:
        return self._clients[client].subscribed()

    def enable_loggers(self, logger: Optional[Union[logging.Logger, logging.LoggerAdapter]] = None):
        for client_name in self._clients:
            self._clients[client_name].enable_logger(logger)

    def disable_loggers(self):
        for client_name in self._clients:
            self._clients[client_name].disable_logger()

    def client_wrapper(self, client: str) -> MQTTClientWrapper:
        return self._clients[client]
