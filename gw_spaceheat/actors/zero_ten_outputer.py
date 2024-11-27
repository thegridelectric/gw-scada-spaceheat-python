"""Implements Dfr Actors"""
import time
from typing import cast

from gwproactor import Actor, ServicesInterface
from gwproactor.message import Message
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
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
        self.node
        self.dfr_multiplexer = self.layout.node(H0N.zero_ten_out_multiplexer)

    def _process_analog_dispatch(self, dispatch: AnalogDispatch) -> None:
        from_node = self.layout.node_by_handle(dispatch.FromHandle)
        if not from_node:
            self.log(f"Ignoring dispatch from  handle {dispatch.FromHandle} - not in layout!!")
            return
        if dispatch.ToHandle != self.node.handle:
            self.log(f"Ignoring dispatch {dispatch} - ToName is not {self.name}!")
            return
        if dispatch.AboutName != self.node.name:
            self.log(f"Ignoring dispatch {dispatch} -- expect AboutName to be about me")
        if dispatch.Value not in range(101):
            self.log(
                f"Igonring dispatch {dispatch} - range out of value. Should be 0-100"
            )
        self.log(f"Got AnalogDispatch from {from_node.name}")
        # self.log(f"Sending {dispatch.Value} to dfr multiplexer")
        self._send_to(
            self.dfr_multiplexer,
            AnalogDispatch(
                FromHandle=self.node.handle,
                ToHandle=self.dfr_multiplexer.handle,
                AboutName=self.name,
                Value=dispatch.Value,
                TriggerId=dispatch.TriggerId,
                UnixTimeMs=int(time.time() * 1000),
            ),
        )

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message, AnalogDispatch):
            return self._process_analog_dispatch(
               message
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
