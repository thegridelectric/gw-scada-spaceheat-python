"""Base for gt.driver.booleanactuator.cmd.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format


class GtDriverBooleanactuatorCmdBase(NamedTuple):
    RelayState: int  #
    ShNodeAlias: str  #
    CommandTimeUnixMs: int  #
    TypeAlias: str = "gt.driver.booleanactuator.cmd.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.RelayState, int):
            errors.append(
                f"RelayState {self.RelayState} must have type int."
            )
        if not property_format.is_bit(self.RelayState):
            errors.append(
                f"RelayState {self.RelayState}"
                " must have format Bit"
            )
        if not isinstance(self.ShNodeAlias, str):
            errors.append(
                f"ShNodeAlias {self.ShNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.ShNodeAlias):
            errors.append(
                f"ShNodeAlias {self.ShNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.CommandTimeUnixMs, int):
            errors.append(
                f"CommandTimeUnixMs {self.CommandTimeUnixMs} must have type int."
            )
        if not property_format.is_reasonable_unix_time_ms(self.CommandTimeUnixMs):
            errors.append(
                f"CommandTimeUnixMs {self.CommandTimeUnixMs}"
                " must have format ReasonableUnixTimeMs"
            )
        if self.TypeAlias != "gt.driver.booleanactuator.cmd.100":
            errors.append(
                f"Type requires TypeAlias of gt.driver.booleanactuator.cmd.100, not {self.TypeAlias}."
            )

        return errors
