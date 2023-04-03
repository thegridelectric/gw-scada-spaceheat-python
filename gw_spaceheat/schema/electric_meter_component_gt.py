"""Type electric.meter.component.gt, version 000"""
import json
from typing import Any, Dict, List, Literal, Optional

from data_classes.components.electric_meter_component import \
    ElectricMeterComponent
from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, root_validator, validator
from schema.egauge_io import EgaugeIo, EgaugeIo_Maker
from schema.telemetry_reporting_config import (TelemetryReportingConfig,
                                               TelemetryReportingConfig_Maker)


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"{v} split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of {v} are not all hex")
    if len(x[0]) != 8:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")


class ElectricMeterComponentGt(BaseModel):
    """Type for tracking Electric Meter Components.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and
    abstractions for managing relational device data. The Component associated to
    a SpaceheatNode is part of this structure.
    [More info](https://g-node-registry.readthedocs.io/en/latest/component.html).
    """

    ComponentId: str = Field(
        title="ComponentId",
    )
    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    DisplayName: Optional[str] = Field(
        title="Display Name for the Power Meter",
        default=None,
    )
    ConfigList: List[TelemetryReportingConfig] = Field(
        title="List of Data Channel configs ",
        description="This power meter will produce multiple data channels. Each data channel "
        "measures a certain quantities (like power, current) for certain ShNodes "
        "(like a boost element or heat pump).",
    )
    HwUid: Optional[str] = Field(
        title="Unique Hardware Id for the Power Meter",
        default=None,
    )
    ModbusHost: Optional[str] = Field(
        title="Host on LAN when power meter is modbus over Ethernet",
        default=None,
    )
    ModbusPort: Optional[int] = Field(
        title="ModbusPort",
        default=None,
    )
    EgaugeIoList: List[EgaugeIo] = Field(
        title="Bijecton from EGauge4030 input to ConfigList output",
        description="This should be empty unless the MakeModel of the corresponding component attribute "
        "class is EGauge 4030. The channels that can be read from an EGauge 4030 are "
        "configurable by the person who installs the device. The information is encapsulated "
        "in a modbus map provided by eGauge as a csv from a device-specific API. The "
        "EGaugeIoList maps the data from this map to the data that the SCADA expects to see.",
    )
    TypeName: Literal["electric.meter.component.gt"] = "electric.meter.component.gt"
    Version: str = "000"

    @validator("ComponentId")
    def _check_component_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("ComponentAttributeClassId")
    def _check_component_attribute_class_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentAttributeClassId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("ConfigList")
    def _check_config_list(cls, v: List) -> List:
        for elt in v:
            if not isinstance(elt, TelemetryReportingConfig):
                raise ValueError(
                    f"elt {elt} of ConfigList must have type TelemetryReportingConfig."
                )
        return v

    @validator("EgaugeIoList")
    def _check_egauge_io_list(cls, v: List) -> List:
        for elt in v:
            if not isinstance(elt, EgaugeIo):
                raise ValueError(f"elt {elt} of EgaugeIoList must have type EgaugeIo.")
        return v

    @root_validator
    def check_axiom_1(cls, v: dict) -> dict:
        """
        Axiom 1: Modbus consistency.
        ModbusHost is None if and only if ModbusPort is None
        """
        # TODO: Implement check for axiom 1"
        ModbusHost = v.get("ModbusHost", None)
        ModbusPort = v.get("ModbusHost", None)
        if ModbusHost is None and not (ModbusPort is None):
            raise ValueError("Axiom 1: ModbusHost None iff ModbusPort None! ")
        if not (ModbusHost is None) and ModbusPort is None:
            raise ValueError("Axiom 1: ModbusHost None iff ModbusPort None! ")
        return v

    @root_validator
    def check_axiom_2(cls, v: dict) -> dict:
        """
        Axiom 2: Egauge4030 consistency.
        If the EgaugeIoList has non-zero length, then the ModbusHost is not None and
        the set of output configs is equal to ConfigList as a set
        """
        # TODO: Implement check for axiom 2"
        EgaugeIoList = v.get("EgaugeIoList", None)
        ModbusHost = v.get("ModbusHost", None)
        ConfigList = v.get("ConfigList", None)
        if len(EgaugeIoList) == 0:
            return v

        if ModbusHost is None:
            raise ValueError(
                f"Axiom 2: If EgaugeIoList has non-zero length then ModbusHost must exist!"
            )
        output_configs = set(map(lambda x: x.OutputConfig, EgaugeIoList))
        if output_configs != set(ConfigList):
            raise ValueError(
                "Axiom 2: If EgaugeIoList has non-zero length then then the set of"
                "output configs must equal ConfigList as a set"
            )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        if d["DisplayName"] is None:
            del d["DisplayName"]

        # Recursively call as_dict() for the SubTypes
        config_list = []
        for elt in self.ConfigList:
            config_list.append(elt.as_dict())
        d["ConfigList"] = config_list
        if d["HwUid"] is None:
            del d["HwUid"]
        if d["ModbusHost"] is None:
            del d["ModbusHost"]
        if d["ModbusPort"] is None:
            del d["ModbusPort"]

        # Recursively call as_dict() for the SubTypes
        egauge_io_list = []
        for elt in self.EgaugeIoList:
            egauge_io_list.append(elt.as_dict())
        d["EgaugeIoList"] = egauge_io_list
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class ElectricMeterComponentGt_Maker:
    type_name = "electric.meter.component.gt"
    version = "000"

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str],
        config_list: List[TelemetryReportingConfig],
        hw_uid: Optional[str],
        modbus_host: Optional[str],
        modbus_port: Optional[int],
        egauge_io_list: List[EgaugeIo],
    ):

        self.tuple = ElectricMeterComponentGt(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            DisplayName=display_name,
            ConfigList=config_list,
            HwUid=hw_uid,
            ModbusHost=modbus_host,
            ModbusPort=modbus_port,
            EgaugeIoList=egauge_io_list,
        )

    @classmethod
    def tuple_to_type(cls, tuple: ElectricMeterComponentGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ElectricMeterComponentGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> ElectricMeterComponentGt:
        d2 = dict(d)
        if "ComponentId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentId")
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "ConfigList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ConfigList")
        config_list = []
        if not isinstance(d2["ConfigList"], List):
            raise MpSchemaError("ConfigList must be a List!")
        for elt in d2["ConfigList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of ConfigList must be "
                    "TelemetryReportingConfig but not even a dict!"
                )
            config_list.append(TelemetryReportingConfig_Maker.dict_to_tuple(elt))
        d2["ConfigList"] = config_list
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "ModbusHost" not in d2.keys():
            d2["ModbusHost"] = None
        if "ModbusPort" not in d2.keys():
            d2["ModbusPort"] = None
        if "EgaugeIoList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing EgaugeIoList")
        if "EgaugeIoList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing EgaugeIoList")
        egauge_io_list = []
        if not isinstance(d2["EgaugeIoList"], List):
            raise MpSchemaError("EgaugeIoList must be a List!")
        for elt in d2["EgaugeIoList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of EgaugeIoList must be "
                    "EgaugeIo but not even a dict!"
                )
            egauge_io_list.append(EgaugeIo_Maker.dict_to_tuple(elt))
        d2["EgaugeIoList"] = egauge_io_list
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return ElectricMeterComponentGt(
            ComponentId=d2["ComponentId"],
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            DisplayName=d2["DisplayName"],
            ConfigList=d2["ConfigList"],
            HwUid=d2["HwUid"],
            ModbusHost=d2["ModbusHost"],
            ModbusPort=d2["ModbusPort"],
            EgaugeIoList=d2["EgaugeIoList"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: ElectricMeterComponentGt) -> ElectricMeterComponent:
        if t.ComponentId in ElectricMeterComponent.by_id.keys():
            dc = ElectricMeterComponent.by_id[t.ComponentId]
        else:
            dc = ElectricMeterComponent(
                component_id=t.ComponentId,
                component_attribute_class_id=t.ComponentAttributeClassId,
                display_name=t.DisplayName,
                config_list=t.ConfigList,
                hw_uid=t.HwUid,
                modbus_host=t.ModbusHost,
                modbus_port=t.ModbusPort,
                egauge_io_list=t.EgaugeIoList,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricMeterComponent) -> ElectricMeterComponentGt:
        t = ElectricMeterComponentGt_Maker(
            component_id=dc.component_id,
            component_attribute_class_id=dc.component_attribute_class_id,
            display_name=dc.display_name,
            config_list=dc.config_list,
            hw_uid=dc.hw_uid,
            modbus_host=dc.modbus_host,
            modbus_port=dc.modbus_port,
            egauge_io_list=dc.egauge_io_list,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ElectricMeterComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ElectricMeterComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> ElectricMeterComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
