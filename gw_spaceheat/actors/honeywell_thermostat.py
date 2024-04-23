import functools
from typing import Optional
from enum import Enum

from gwproto.types.hubitat_poller_gt import MakerAPIAttributeGt

from actors.hubitat_poller import HubitatPoller
from actors.hubitat_interface import default_mapping_converter
from actors.hubitat_interface import HubitatWebEventListenerInterface
from actors.hubitat_interface import ValueConverter

class HoneywellThermostatOperatingState(Enum):
    idle = 0
    heating = 1
    pending_heat = 2
    # We decided to ignore these
    # pending_cool = 3
    # vent_economizer = 4
    # cooling = 5
    # fan_only = 6

    @classmethod
    def mapping(cls) -> dict[str, int]:
        return {
            name.replace("_", " "): value.value
            for name, value in HoneywellThermostatOperatingState.__members__.items()
        }

class HoneywellThermostat(HubitatPoller, HubitatWebEventListenerInterface):

    def _make_non_numerical_value_converter(self, attribute: MakerAPIAttributeGt) -> Optional[ValueConverter]: # noqa
        if attribute.attribute_name == "thermostatOperatingState":
            return functools.partial(
                default_mapping_converter,
                mapping=HoneywellThermostatOperatingState.mapping()
            )
        return None