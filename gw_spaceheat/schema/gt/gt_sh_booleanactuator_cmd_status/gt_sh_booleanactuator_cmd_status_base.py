"""Base for gt.sh.booleanactuator.cmd.status.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format


class GtShBooleanactuatorCmdStatusBase(NamedTuple):
    ShNodeAlias: str  #
    RelayStateCommandList: List[int]
    CommandTimeUnixMsList: List[int]
    TypeAlias: str = "gt.sh.booleanactuator.cmd.status.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ShNodeAlias, str):
            errors.append(
                f"ShNodeAlias {self.ShNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.ShNodeAlias):
            errors.append(
                f"ShNodeAlias {self.ShNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.RelayStateCommandList, list):
            errors.append(
                f"RelayStateCommandList {self.RelayStateCommandList} must have type list."
            )
        else:
            for elt in self.RelayStateCommandList:
                if not isinstance(elt, int):
                    errors.append(
                        f"elt {elt} of RelayStateCommandList must have type int."
                    )
                if not property_format.is_bit(elt):
                    errors.append(
                        f"elt {elt} of RelayStateCommandList must have format Bit"
                    )
        if not isinstance(self.CommandTimeUnixMsList, list):
            errors.append(
                f"CommandTimeUnixMsList {self.CommandTimeUnixMsList} must have type list."
            )
        else:
            for elt in self.CommandTimeUnixMsList:
                if not isinstance(elt, int):
                    errors.append(
                        f"elt {elt} of CommandTimeUnixMsList must have type int."
                    )
                if not property_format.is_reasonable_unix_time_ms(elt):
                    errors.append(
                        f"elt {elt} of CommandTimeUnixMsList must have format ReasonableUnixTimeMs"
                    )
        if self.TypeAlias != "gt.sh.booleanactuator.cmd.status.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.booleanactuator.cmd.status.100, not {self.TypeAlias}."
            )

        return errors
