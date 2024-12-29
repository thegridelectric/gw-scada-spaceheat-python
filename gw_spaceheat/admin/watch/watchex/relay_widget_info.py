from typing import Optional

from pydantic import BaseModel

from admin.watch.clients.relay_client import RelayEnergized
from admin.watch.clients.relay_client import RelayState
from admin.watch.widgets.relay2 import RelayWidgetConfig


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
