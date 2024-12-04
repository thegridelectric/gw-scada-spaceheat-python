from typing import Any, cast

from actors.config import ScadaSettings
from gwproactor import Actor, ServicesInterface
from gwproto import Message
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode


class ScadaActor(Actor):
    layout: House0Layout
    node: ShNode

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)

    @property
    def node(self) -> ShNode:
        # note: self._node exists in proactor but may be stale
        return self.layout.node(self.name)

    @property
    def layout(self) -> House0Layout:
        try:
            layout = cast(House0Layout, self.services.hardware_layout)
        except Exception as e:
            raise Exception(f"Failed to cast layout as House0Layout!! {e}")
        return layout

    @property
    def settings(self) -> ScadaSettings:
        return self.services.settings

    @property
    def primary_scada(self) -> ShNode:
        return self.layout.node(H0N.primary_scada)

    def boss(self) -> ShNode:
        if ".".join(self.node.handle.split(".")[:-1]) == "":
            return self.node

        boss_handle = ".".join(self.node.handle.split(".")[:-1])
        return next(n for n in self.layout.nodes.values() if n.handle == boss_handle)

    def is_boss_of(self, node: ShNode) -> bool:
        immediate_boss = ".".join(node.Handle.split(".")[:-1])
        return immediate_boss == self.node.handle

    def direct_reports(self) -> list[ShNode]:
        return [n for n in self.layout.nodes.values() if self.is_boss_of(n)]

    def _send_to(self, dst: ShNode, payload: Any) -> None:
        if dst is None:
            return
        message = Message(Src=self.name, Dst=dst.name, Payload=payload)
        if dst.name in set(self.services._communicators.keys()) | {
            self.services.name
        }:  # noqa: SLF001
            self.services.send(message)
        elif dst.Name == H0N.admin:
            self.services._links.publish_message(
                self.services.ADMIN_MQTT, message
            )  # noqa: SLF001
        elif dst.Name == H0N.atn:
            self.services._links.publish_upstream(payload)  # noqa: SLF001
        else:
            self.services._links.publish_message(
                self.services.LOCAL_MQTT, message
            )  # noqa: SLF001

    def log(self, note: str) -> None:
        log_str = f"[{self.name}] {note}"
        self.services.logger.error(log_str)
