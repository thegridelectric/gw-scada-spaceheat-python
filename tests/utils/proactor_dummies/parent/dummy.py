"""Scada implementation"""
from typing import cast

from proactor.persister import SimpleDirectoryWriter

from gwproto import Decoders
from gwproto import create_message_payload_discriminator
from gwproto import MQTTCodec
from gwproto import MQTTTopic

from proactor.mqtt import QOS
from proactor.message import Message

from proactor.proactor_implementation import Proactor

from tests.utils.proactor_dummies.names import DUMMY_CHILD_NAME
from tests.utils.proactor_dummies.parent.config import DummyParentSettings

ParentMessageDecoder = create_message_payload_discriminator(
    model_name="ParentMessageDecoder",
    module_names=["gwproto.messages"],
)


class ParentMQTTCodec(MQTTCodec):

    def __init__(self):
        super().__init__(Decoders.from_objects(message_payload_discriminator=ParentMessageDecoder))

    def validate_source_alias(self, source_alias: str):
        if source_alias != DUMMY_CHILD_NAME:
            raise Exception(f"alias {source_alias} not my Scada!")

class DummyParent(Proactor):
    CHILD_MQTT = "child"

    def __init__(
        self,
        name: str,
        settings: DummyParentSettings,
    ):
        super().__init__(name=name, settings=settings)
        self._add_mqtt_client(self.CHILD_MQTT, self.settings.child_mqtt, ParentMQTTCodec(), primary_peer=True)
        self._mqtt_clients.subscribe(
            self.CHILD_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), DUMMY_CHILD_NAME),
            QOS.AtMostOnce,
        )

    @classmethod
    def make_event_persister(cls, settings:DummyParentSettings) -> SimpleDirectoryWriter:
        return SimpleDirectoryWriter(settings.paths.event_dir)

    @property
    def publication_name(self) -> str:
        return self.name

    @property
    def settings(self) -> DummyParentSettings:
        return cast(DummyParentSettings, self._settings)


