import asyncio
from enum import auto
import uuid
import time
from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface
from result import Ok, Result
from gwproto import Message
from gwproto.message import Header
from transitions import Machine
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.house_0_names import H0N
from gwproto.enums import ChangeRelayState
from gwproto.named_types import FsmEvent
import pendulum

class HomeAloneState(GwStrEnum):
    WaitingForTemperaturesOnPeak = auto()
    WaitingForTemperaturesOffPeak = auto()
    HpOnStoreOff = auto()
    HpOnStoreCharge = auto()
    HpOffStoreOff = auto()
    HpOffStoreDischarge = auto()

    @classmethod
    def enum_name(cls) -> str:
        "home.alone.state"


class HomeAloneEvent(GwStrEnum):
    OnPeakStart = auto()
    OffPeakStart = auto()
    OnPeakBufferFull = auto()
    OffPeakBufferFullStorageNotReady = auto()
    OffPeakBufferFullStorageReady = auto()
    OffPeakBufferEmpty = auto()
    OnPeakBufferEmpty = auto()
    OffPeakStorageReady = auto()
    OffPeakStorageNotReady = auto()
    TemperaturesAvailable = auto()

    @classmethod
    def enum_name(cls) -> str:
        "home.alone.event"
    

class RealHomeAlone(Actor):
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False
    

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="HomeAlone keepalive")
        )
    
    def stop(self) -> None:
        self._stop_requested = True
    
    async def join(self):
        ...
    
    def process_message(self, message: Message) -> Result[bool, BaseException]:
        return Ok()
    
    async def main(self):
        while not self._stop_requested:
            print(f"[{self.name}] In main loop. Sleeping for 5")
            await asyncio.sleep(5)


