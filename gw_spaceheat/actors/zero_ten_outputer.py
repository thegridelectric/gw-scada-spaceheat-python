"""Implements Dfr Actors"""
import time
from typing import cast

from gwproactor import QOS, Actor, ServicesInterface
from gwproactor.message import Message
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.message import Header
from gwproto.named_types import AnalogDispatch
from result import Err, Result


class ZeroTenOutputer(Actor):
    def __init__(
        self,
        name: str,
        services: ServicesInterface,
    ):
        self.layout = cast(House0Layout, services.hardware_layout)
        super().__init__(name, services)
        self.dfr_multiplexer = self.layout.node(H0N.zero_ten_out_multiplexer)

    def _process_analog_dispatch(self, dispatch: AnalogDispatch) -> None:
        if dispatch.FromName not in self.layout.nodes:
            self.log(f"Ignoring dispatch from {dispatch.FromName} - not in layout!!")
            return
        if dispatch.ToName != self.name:
            self.log(f"Ignoring dispatch {dispatch} - ToName is not {self.name}!")
            return
        if dispatch.ToName != dispatch.AboutName:
            self.log(f"Ignoring dispatch {dispatch} -- ToName should equal AboutName")
        if dispatch.Value not in range(101):
            self.log(
                f"Igonring dispatch {dispatch} - range out of value. Should be 0-100"
            )
        self.log(f"Got AnalogDispatch from {dispatch.FromName}")
        self.log(f"Sending {dispatch.Value} to dfr multiplexer")
        self._send_to(
            self.dfr_multiplexer,
            AnalogDispatch(
                FromName=self.name,
                ToName=self.dfr_multiplexer.name,
                AboutName=self.name,
                Value=dispatch.Value,
                MessageId=dispatch.MessageId,
                UnixTimeMs=int(time.time() * 1000),
            ),
        )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, AnalogDispatch):
            return self._process_analog_dispatch(
                from_name=message.Header.Src, message=message.Payload
            )
        return Err(
            ValueError(f"{self.name} receieved unexpected message: {message.Header}")
        )

    def start(self) -> None:
        ...

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        ...

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...

    def _send_to(self, dst: ShNode, payload) -> None:
        if (
            dst.name == self.services.name
            or self.services.get_communicator(dst.name) is not None
        ):
            self._send(
                Message(
                    header=Header(
                        Src=self.name,
                        Dst=dst.name,
                        MessageType=payload.TypeName,
                    ),
                    Payload=payload,
                )
            )
        else:
            # Otherwise send via local mqtt
            message = Message(Src=self.name, Dst=dst.name, Payload=payload)
            return self.services.publish_message(  # noqa
                self.services.LOCAL_MQTT,  # noqa
                message,
                qos=QOS.AtMostOnce,
            )

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)
