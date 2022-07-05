"""Base for gt.dispatch.boolean.local.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format


class GtDispatchBooleanLocalBase(NamedTuple):
    SendTimeUnixMs: int  #
    FromNodeAlias: str  #
    AboutNodeAlias: str  #
    RelayState: int  #
    TypeAlias: str = "gt.dispatch.boolean.local.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.SendTimeUnixMs, int):
            errors.append(
                f"SendTimeUnixMs {self.SendTimeUnixMs} must have type int."
            )
        if not property_format.is_reasonable_unix_time_ms(self.SendTimeUnixMs):
            errors.append(
                f"SendTimeUnixMs {self.SendTimeUnixMs}"
                " must have format ReasonableUnixTimeMs"
            )
        if not isinstance(self.FromNodeAlias, str):
            errors.append(
                f"FromNodeAlias {self.FromNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.FromNodeAlias):
            errors.append(
                f"FromNodeAlias {self.FromNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.AboutNodeAlias, str):
            errors.append(
                f"AboutNodeAlias {self.AboutNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.AboutNodeAlias):
            errors.append(
                f"AboutNodeAlias {self.AboutNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.RelayState, int):
            errors.append(
                f"RelayState {self.RelayState} must have type int."
            )
        if not property_format.is_bit(self.RelayState):
            errors.append(
                f"RelayState {self.RelayState}"
                " must have format Bit"
            )
        if self.TypeAlias != "gt.dispatch.boolean.local.100":
            errors.append(
                f"Type requires TypeAlias of gt.dispatch.boolean.local.100, not {self.TypeAlias}."
            )

        return errors
