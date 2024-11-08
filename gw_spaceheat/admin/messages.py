import uuid
from typing import Literal

from gwproto.messages import EventBase
from pydantic import BaseModel, Field

class RelayInfo(BaseModel):
    RelayName: str = ""
    Closed: bool = False

class RelayInfoReported(RelayInfo):
    CurrentChangeMismatch: bool = False
    MismatchCount: int = 0

class RelayStates(BaseModel):
    TotalChangeMismatches: int = 0
    Relays: dict[str, RelayInfoReported] = {}
    TypeName: Literal["gridworks.dummy.relay.states"] = "gridworks.dummy.relay.states"

class AdminInfo(BaseModel):
    User: str
    SrcMachine: str

class RelayReportEvent(EventBase):
    relay_name: str = ""
    closed: bool = False
    changed: bool = False
    TypeName: Literal["gridworks.event.relay.report"] = "gridworks.event.relay.report"


class AdminCommandSetRelay(BaseModel):
    CommandInfo: AdminInfo
    RelayInfo: RelayInfo
    MessageId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    TypeName: Literal["gridworks.admin.command.set.relay"] = (
        "gridworks.admin.command.set.relay"
    )


class AdminCommandReadRelays(BaseModel):
    CommandInfo: AdminInfo
    MessageId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    TypeName: Literal["gridworks.admin.command.read.relays"] = (
        "gridworks.admin.command.read.relays"
    )


class AdminSetRelayEvent(EventBase):
    command: AdminCommandSetRelay
    TypeName: Literal["gridworks.event.admin.command.set.relay"] = (
        "gridworks.event.admin.command.set.relay"
    )

