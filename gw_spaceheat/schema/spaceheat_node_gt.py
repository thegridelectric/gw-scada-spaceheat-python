"""Type spaceheat.node.gt, version 100"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from data_classes.sh_node import ShNode
from enums import ActorClass as EnumActorClass
from enums import Role as EnumRole
from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError
from gwproto.message import as_enum
from pydantic import BaseModel, Field, validator


class ShActorClass000SchemaEnum:
    enum_name: str = "sh.actor.class.000"
    symbols: List[str] = [
        "00000000",
        "6d37aa41",
        "32d3d19f",
        "fddd0064",
        "2ea112b9",
        "b103058f",
        "dae4b2f0",
        "7c483ad0",
        "4a9c1785",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class ShActorClass000(StrEnum):
    NoActor = auto()
    Scada = auto()
    HomeAlone = auto()
    BooleanActuator = auto()
    PowerMeter = auto()
    Atn = auto()
    SimpleSensor = auto()
    MultipurposeSensor = auto()
    Thermostat = auto()

    @classmethod
    def default(cls) -> "ShActorClass000":
        return cls.NoActor

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class ActorClassMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> EnumActorClass:
        if not ShActorClass000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to ShActorClass000 symbols")
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, EnumActorClass, EnumActorClass.default())

    @classmethod
    def local_to_type(cls, actor_class: EnumActorClass) -> str:
        if not isinstance(actor_class, EnumActorClass):
            raise MpSchemaError(f"{actor_class} must be of type {EnumActorClass}")
        versioned_enum = as_enum(
            actor_class, ShActorClass000, ShActorClass000.default()
        )
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, ShActorClass000] = {
        "00000000": ShActorClass000.NoActor,
        "6d37aa41": ShActorClass000.Scada,
        "32d3d19f": ShActorClass000.HomeAlone,
        "fddd0064": ShActorClass000.BooleanActuator,
        "2ea112b9": ShActorClass000.PowerMeter,
        "b103058f": ShActorClass000.Atn,
        "dae4b2f0": ShActorClass000.SimpleSensor,
        "7c483ad0": ShActorClass000.MultipurposeSensor,
        "4a9c1785": ShActorClass000.Thermostat,
    }

    versioned_enum_to_type_dict: Dict[ShActorClass000, str] = {
        ShActorClass000.NoActor: "00000000",
        ShActorClass000.Scada: "6d37aa41",
        ShActorClass000.HomeAlone: "32d3d19f",
        ShActorClass000.BooleanActuator: "fddd0064",
        ShActorClass000.PowerMeter: "2ea112b9",
        ShActorClass000.Atn: "b103058f",
        ShActorClass000.SimpleSensor: "dae4b2f0",
        ShActorClass000.MultipurposeSensor: "7c483ad0",
        ShActorClass000.Thermostat: "4a9c1785",
    }


class ShNodeRole000SchemaEnum:
    enum_name: str = "sh.node.role.000"
    symbols: List[str] = [
        "00000000",
        "d0afb424",
        "863e50d1",
        "6ddff83b",
        "9ac68b6e",
        "99c5f326",
        "57b788ee",
        "3ecfe9b8",
        "73308a1f",
        "c480f612",
        "fec74958",
        "5938bf1f",
        "ece3b600",
        "65725f44",
        "fe3cbdd5",
        "05fdd645",
        "6896109b",
        "b0eaf2ba",
        "661d7e73",
        "dd975b31",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class ShNodeRole000(StrEnum):
    Unknown = auto()
    Scada = auto()
    HomeAlone = auto()
    Atn = auto()
    PowerMeter = auto()
    BoostElement = auto()
    BooleanActuator = auto()
    DedicatedThermalStore = auto()
    TankWaterTempSensor = auto()
    PipeTempSensor = auto()
    RoomTempSensor = auto()
    OutdoorTempSensor = auto()
    PipeFlowMeter = auto()
    HeatedSpace = auto()
    HydronicPipe = auto()
    BaseboardRadiator = auto()
    RadiatorFan = auto()
    CirculatorPump = auto()
    MultiChannelAnalogTempSensor = auto()
    Outdoors = auto()

    @classmethod
    def default(cls) -> "ShNodeRole000":
        return cls.Unknown

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class RoleMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> EnumRole:
        if not ShNodeRole000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to ShNodeRole000 symbols")
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, EnumRole, EnumRole.default())

    @classmethod
    def local_to_type(cls, role: EnumRole) -> str:
        if not isinstance(role, EnumRole):
            raise MpSchemaError(f"{role} must be of type {EnumRole}")
        versioned_enum = as_enum(role, ShNodeRole000, ShNodeRole000.default())
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, ShNodeRole000] = {
        "00000000": ShNodeRole000.Unknown,
        "d0afb424": ShNodeRole000.Scada,
        "863e50d1": ShNodeRole000.HomeAlone,
        "6ddff83b": ShNodeRole000.Atn,
        "9ac68b6e": ShNodeRole000.PowerMeter,
        "99c5f326": ShNodeRole000.BoostElement,
        "57b788ee": ShNodeRole000.BooleanActuator,
        "3ecfe9b8": ShNodeRole000.DedicatedThermalStore,
        "73308a1f": ShNodeRole000.TankWaterTempSensor,
        "c480f612": ShNodeRole000.PipeTempSensor,
        "fec74958": ShNodeRole000.RoomTempSensor,
        "5938bf1f": ShNodeRole000.OutdoorTempSensor,
        "ece3b600": ShNodeRole000.PipeFlowMeter,
        "65725f44": ShNodeRole000.HeatedSpace,
        "fe3cbdd5": ShNodeRole000.HydronicPipe,
        "05fdd645": ShNodeRole000.BaseboardRadiator,
        "6896109b": ShNodeRole000.RadiatorFan,
        "b0eaf2ba": ShNodeRole000.CirculatorPump,
        "661d7e73": ShNodeRole000.MultiChannelAnalogTempSensor,
        "dd975b31": ShNodeRole000.Outdoors,
    }

    versioned_enum_to_type_dict: Dict[ShNodeRole000, str] = {
        ShNodeRole000.Unknown: "00000000",
        ShNodeRole000.Scada: "d0afb424",
        ShNodeRole000.HomeAlone: "863e50d1",
        ShNodeRole000.Atn: "6ddff83b",
        ShNodeRole000.PowerMeter: "9ac68b6e",
        ShNodeRole000.BoostElement: "99c5f326",
        ShNodeRole000.BooleanActuator: "57b788ee",
        ShNodeRole000.DedicatedThermalStore: "3ecfe9b8",
        ShNodeRole000.TankWaterTempSensor: "73308a1f",
        ShNodeRole000.PipeTempSensor: "c480f612",
        ShNodeRole000.RoomTempSensor: "fec74958",
        ShNodeRole000.OutdoorTempSensor: "5938bf1f",
        ShNodeRole000.PipeFlowMeter: "ece3b600",
        ShNodeRole000.HeatedSpace: "65725f44",
        ShNodeRole000.HydronicPipe: "fe3cbdd5",
        ShNodeRole000.BaseboardRadiator: "05fdd645",
        ShNodeRole000.RadiatorFan: "6896109b",
        ShNodeRole000.CirculatorPump: "b0eaf2ba",
        ShNodeRole000.MultiChannelAnalogTempSensor: "661d7e73",
        ShNodeRole000.Outdoors: "dd975b31",
    }


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


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods,
    most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate {v} into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(f"Most significant word of {v} must start with alphabet char.")
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of {v} split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of {v} must be lowercase.")


class SpaceheatNodeGt(BaseModel):
    """Spaceheat Node.

    Type for tracking information about a Spaceheat Node.
    [More info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node.html).
    """

    ShNodeId: str = Field(
        title="ShNodeId",
    )
    Alias: str = Field(
        title="Alias",
    )
    ActorClass: EnumActorClass = Field(
        title="ActorClass",
    )
    Role: EnumRole = Field(
        title="Role",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    ComponentId: Optional[str] = Field(
        title="ComponentId",
    )
    ReportingSamplePeriodS: Optional[int] = Field(
        title="ReportingSamplePeriodS",
        default=None,
    )
    RatedVoltageV: Optional[int] = Field(
        title="RatedVoltageV",
        default=None,
    )
    TypicalVoltageV: Optional[int] = Field(
        title="TypicalVoltageV",
        default=None,
    )
    InPowerMetering: Optional[bool] = Field(
        title="InPowerMetering",
        default=None,
    )
    TypeName: Literal["spaceheat.node.gt"] = "spaceheat.node.gt"
    Version: str = "100"

    @validator("ShNodeId")
    def _check_sh_node_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ShNodeId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("Alias")
    def _check_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"Alias failed LeftRightDot format validation: {e}")
        return v

    @validator("ActorClass")
    def _check_actor_class(cls, v: EnumActorClass) -> EnumActorClass:
        return as_enum(v, EnumActorClass, EnumActorClass.NoActor)

    @validator("Role")
    def _check_role(cls, v: EnumRole) -> EnumRole:
        return as_enum(v, EnumRole, EnumRole.Unknown)

    @validator("ComponentId")
    def _check_component_id(cls, v: str) -> str:
        if v is None:
            return v
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["ActorClass"]
        ActorClass = as_enum(self.ActorClass, EnumActorClass, EnumActorClass.default())
        d["ActorClassGtEnumSymbol"] = ActorClassMap.local_to_type(ActorClass)
        del d["Role"]
        Role = as_enum(self.Role, EnumRole, EnumRole.default())
        d["RoleGtEnumSymbol"] = RoleMap.local_to_type(Role)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["ComponentId"] is None:
            del d["ComponentId"]
        if d["ReportingSamplePeriodS"] is None:
            del d["ReportingSamplePeriodS"]
        if d["RatedVoltageV"] is None:
            del d["RatedVoltageV"]
        if d["TypicalVoltageV"] is None:
            del d["TypicalVoltageV"]
        if d["InPowerMetering"] is None:
            del d["InPowerMetering"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa


class SpaceheatNodeGt_Maker:
    type_name = "spaceheat.node.gt"
    version = "100"

    def __init__(
        self,
        sh_node_id: str,
        alias: str,
        actor_class: EnumActorClass,
        role: EnumRole,
        display_name: Optional[str],
        component_id: Optional[str],
        reporting_sample_period_s: Optional[int],
        rated_voltage_v: Optional[int],
        typical_voltage_v: Optional[int],
        in_power_metering: Optional[bool],
    ):

        self.tuple = SpaceheatNodeGt(
            ShNodeId=sh_node_id,
            Alias=alias,
            ActorClass=actor_class,
            Role=role,
            DisplayName=display_name,
            ComponentId=component_id,
            ReportingSamplePeriodS=reporting_sample_period_s,
            RatedVoltageV=rated_voltage_v,
            TypicalVoltageV=typical_voltage_v,
            InPowerMetering=in_power_metering,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: SpaceheatNodeGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> SpaceheatNodeGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> SpaceheatNodeGt:
        d2 = dict(d)
        if "ShNodeId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ShNodeId")
        if "Alias" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Alias")
        if "ActorClassGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ActorClassGtEnumSymbol")
        if d2["ActorClassGtEnumSymbol"] in ShActorClass000SchemaEnum.symbols:
            d2["ActorClass"] = ActorClassMap.type_to_local(d2["ActorClassGtEnumSymbol"])
        else:
            d2["ActorClass"] = EnumActorClass.default()
        if "RoleGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing RoleGtEnumSymbol")
        if d2["RoleGtEnumSymbol"] in ShNodeRole000SchemaEnum.symbols:
            d2["Role"] = RoleMap.type_to_local(d2["RoleGtEnumSymbol"])
        else:
            d2["Role"] = EnumRole.default()
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "ComponentId" not in d2.keys():
            d2["ComponentId"] = None
        if "ReportingSamplePeriodS" not in d2.keys():
            d2["ReportingSamplePeriodS"] = None
        if "RatedVoltageV" not in d2.keys():
            d2["RatedVoltageV"] = None
        if "TypicalVoltageV" not in d2.keys():
            d2["TypicalVoltageV"] = None
        if "InPowerMetering" not in d2.keys():
            d2["InPowerMetering"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return SpaceheatNodeGt(
            ShNodeId=d2["ShNodeId"],
            Alias=d2["Alias"],
            ActorClass=d2["ActorClass"],
            Role=d2["Role"],
            DisplayName=d2["DisplayName"],
            ComponentId=d2["ComponentId"],
            ReportingSamplePeriodS=d2["ReportingSamplePeriodS"],
            RatedVoltageV=d2["RatedVoltageV"],
            TypicalVoltageV=d2["TypicalVoltageV"],
            InPowerMetering=d2["InPowerMetering"],
            TypeName=d2["TypeName"],
            Version="100",
        )

    @classmethod
    def tuple_to_dc(cls, t: SpaceheatNodeGt) -> ShNode:
        if t.ShNodeId in ShNode.by_id.keys():
            dc = ShNode.by_id[t.ShNodeId]
        else:
            dc = ShNode(
                sh_node_id=t.ShNodeId,
                alias=t.Alias,
                actor_class=t.ActorClass,
                role=t.Role,
                display_name=t.DisplayName,
                component_id=t.ComponentId,
                reporting_sample_period_s=t.ReportingSamplePeriodS,
                rated_voltage_v=t.RatedVoltageV,
                typical_voltage_v=t.TypicalVoltageV,
                in_power_metering=t.InPowerMetering,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ShNode) -> SpaceheatNodeGt:
        t = SpaceheatNodeGt_Maker(
            sh_node_id=dc.sh_node_id,
            alias=dc.alias,
            actor_class=dc.actor_class,
            role=dc.role,
            display_name=dc.display_name,
            component_id=dc.component_id,
            reporting_sample_period_s=dc.reporting_sample_period_s,
            rated_voltage_v=dc.rated_voltage_v,
            typical_voltage_v=dc.typical_voltage_v,
            in_power_metering=dc.in_power_metering,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ShNode:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ShNode) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> ShNode:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
