"""Base for gt.sh.status.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status_maker import GtShBooleanactuatorCmdStatus
from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status_maker import GtShSimpleTelemetryStatus
from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status_maker import GtShMultipurposeTelemetryStatus


class GtShStatusBase(NamedTuple):
    BooleanactuatorCmdList: List[GtShBooleanactuatorCmdStatus]
    SimpleTelemetryList: List[GtShSimpleTelemetryStatus]
    MultipurposeTelemetryList: List[GtShMultipurposeTelemetryStatus]
    SlotStartUnixS: int  #
    AboutGNodeAlias: str  #
    ReportingPeriodS: int  #
    TypeAlias: str = "gt.sh.status.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()

        # Recursively call asdict() for the SubTypes
        booleanactuator_cmd_list = []
        for elt in self.BooleanactuatorCmdList:
            booleanactuator_cmd_list.append(elt.asdict())
        d["BooleanactuatorCmdList"] = booleanactuator_cmd_list

        # Recursively call asdict() for the SubTypes
        simple_telemetry_list = []
        for elt in self.SimpleTelemetryList:
            simple_telemetry_list.append(elt.asdict())
        d["SimpleTelemetryList"] = simple_telemetry_list

        # Recursively call asdict() for the SubTypes
        multipurpose_telemetry_list = []
        for elt in self.MultipurposeTelemetryList:
            multipurpose_telemetry_list.append(elt.asdict())
        d["MultipurposeTelemetryList"] = multipurpose_telemetry_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.BooleanactuatorCmdList, list):
            errors.append(
                f"BooleanactuatorCmdList {self.BooleanactuatorCmdList} must have type list."
            )
        else:
            for elt in self.BooleanactuatorCmdList:
                if not isinstance(elt, GtShBooleanactuatorCmdStatus):
                    errors.append(
                        f"elt {elt} of BooleanactuatorCmdList must have type GtShBooleanactuatorCmdStatus."
                    )
        if not isinstance(self.SimpleTelemetryList, list):
            errors.append(
                f"SimpleTelemetryList {self.SimpleTelemetryList} must have type list."
            )
        else:
            for elt in self.SimpleTelemetryList:
                if not isinstance(elt, GtShSimpleTelemetryStatus):
                    errors.append(
                        f"elt {elt} of SimpleTelemetryList must have type GtShSimpleTelemetryStatus."
                    )
        if not isinstance(self.MultipurposeTelemetryList, list):
            errors.append(
                f"MultipurposeTelemetryList {self.MultipurposeTelemetryList} must have type list."
            )
        else:
            for elt in self.MultipurposeTelemetryList:
                if not isinstance(elt, GtShMultipurposeTelemetryStatus):
                    errors.append(
                        f"elt {elt} of MultipurposeTelemetryList must have type GtShMultipurposeTelemetryStatus."
                    )
        if not isinstance(self.SlotStartUnixS, int):
            errors.append(
                f"SlotStartUnixS {self.SlotStartUnixS} must have type int."
            )
        if not property_format.is_reasonable_unix_time_s(self.SlotStartUnixS):
            errors.append(
                f"SlotStartUnixS {self.SlotStartUnixS}"
                " must have format ReasonableUnixTimeS"
            )
        if not isinstance(self.AboutGNodeAlias, str):
            errors.append(
                f"AboutGNodeAlias {self.AboutGNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.AboutGNodeAlias):
            errors.append(
                f"AboutGNodeAlias {self.AboutGNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(
                f"ReportingPeriodS {self.ReportingPeriodS} must have type int."
            )
        if self.TypeAlias != "gt.sh.status.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.status.100, not {self.TypeAlias}."
            )

        return errors
