from typing import Optional

from pydantic import BaseModel

from admin.watch.clients.relay_client import RelayConfig
from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState

class RelayWidgetConfig(RelayConfig):
    energized_icon: str = "⚡"
    deenergized_icon: str = "-"
    show_icon: bool = True

    @classmethod
    def from_config(
            cls,
            config: RelayConfig,
            energized_icon: str = "⚡",
            deenergized_icon: str = "-",
            show_icon: bool = True,
    ) -> "RelayWidgetConfig":
        return RelayWidgetConfig(
            energized_icon=energized_icon,
            deenergized_icon=deenergized_icon,
            show_icon=show_icon,
            **config.model_dump()
        )

    def get_state_str(self, energized: Optional[bool], *, show_icon: Optional[bool] = None) -> str:
        if energized is None:
            icon = "?"
            description = "?"
        elif energized:
            icon = self.energized_icon
            description = self.energized_description
        else:
            icon = self.deenergized_icon
            description = self.deenergized_description
        if (show_icon is None and self.show_icon) or show_icon is True:
            return f"{icon} / {description}"
        return description


class RelayWidgetInfo(BaseModel):
    config: RelayWidgetConfig = RelayWidgetConfig()
    observed: Optional[RelayState] = None

    @classmethod
    def get_observed_state(cls, observed) -> Optional[bool]:
        if observed is not None:
            return observed.value == RelayEnergized.energized
        return None

    def get_state(self) -> Optional[bool]:
        return self.get_observed_state(self.observed)

    def get_state_str(self) -> str:
        return self.config.get_state_str(self.get_state())

    def get_energize_str(self) -> str:
        return self.config.get_energize_str(True)

    def get_deenergize_str(self) -> str:
        return self.config.get_energize_str(False)
