"""Type gt.powermeter.reporting.config, version 100"""
import json
from typing import Any, Dict, List, Literal, Optional

from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator
from gwproto.types import (
    TelemetryReportingConfig,
    TelemetryReportingConfig_Maker,
)


class GtPowermeterReportingConfig(BaseModel):
    """ """

    ReportingPeriodS: int = Field(
        title="ReportingPeriodS",
    )
    ElectricalQuantityReportingConfigList: List[TelemetryReportingConfig] = Field(
        title="ElectricalQuantityReportingConfigList",
    )
    PollPeriodMs: int = Field(
        title="PollPeriodMs",
    )
    HwUid: Optional[str] = Field(
        title="HwUid",
        default=None,
    )
    TypeName: Literal[
        "gt.powermeter.reporting.config"
    ] = "gt.powermeter.reporting.config"
    Version: str = "100"

    @validator("ElectricalQuantityReportingConfigList")
    def _check_electrical_quantity_reporting_config_list(cls, v: List) -> List:
        for elt in v:
            if not isinstance(elt, TelemetryReportingConfig):
                raise ValueError(
                    f"elt {elt} of ElectricalQuantityReportingConfigList must have type TelemetryReportingConfig."
                )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()

        # Recursively call as_dict() for the SubTypes
        electrical_quantity_reporting_config_list = []
        for elt in self.ElectricalQuantityReportingConfigList:
            electrical_quantity_reporting_config_list.append(elt.as_dict())
        d[
            "ElectricalQuantityReportingConfigList"
        ] = electrical_quantity_reporting_config_list
        if d["HwUid"] is None:
            del d["HwUid"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa


class GtPowermeterReportingConfig_Maker:
    type_name = "gt.powermeter.reporting.config"
    version = "100"

    def __init__(
        self,
        reporting_period_s: int,
        electrical_quantity_reporting_config_list: List[TelemetryReportingConfig],
        poll_period_ms: int,
        hw_uid: Optional[str],
    ):

        self.tuple = GtPowermeterReportingConfig(
            ReportingPeriodS=reporting_period_s,
            ElectricalQuantityReportingConfigList=electrical_quantity_reporting_config_list,
            PollPeriodMs=poll_period_ms,
            HwUid=hw_uid,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtPowermeterReportingConfig) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtPowermeterReportingConfig:
        """
        Given a serialized JSON type object, returns the Python class object
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtPowermeterReportingConfig:
        d2 = dict(d)
        if "ReportingPeriodS" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ReportingPeriodS")
        if "ElectricalQuantityReportingConfigList" not in d2.keys():
            raise MpSchemaError(
                f"dict {d2} missing ElectricalQuantityReportingConfigList"
            )
        electrical_quantity_reporting_config_list = []
        if not isinstance(d2["ElectricalQuantityReportingConfigList"], List):
            raise MpSchemaError("ElectricalQuantityReportingConfigList must be a List!")
        for elt in d2["ElectricalQuantityReportingConfigList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of ElectricalQuantityReportingConfigList must be "
                    "TelemetryReportingConfig but not even a dict!"
                )
            electrical_quantity_reporting_config_list.append(
                TelemetryReportingConfig_Maker.dict_to_tuple(elt)
            )
        d2[
            "ElectricalQuantityReportingConfigList"
        ] = electrical_quantity_reporting_config_list
        if "PollPeriodMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing PollPeriodMs")
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return GtPowermeterReportingConfig(
            ReportingPeriodS=d2["ReportingPeriodS"],
            ElectricalQuantityReportingConfigList=d2[
                "ElectricalQuantityReportingConfigList"
            ],
            PollPeriodMs=d2["PollPeriodMs"],
            HwUid=d2["HwUid"],
            TypeName=d2["TypeName"],
            Version="100",
        )
