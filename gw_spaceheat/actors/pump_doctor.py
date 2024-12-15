import asyncio
import time
from gwproactor import ServicesInterface
from gwproto import Message
from result import Ok, Result
from actors.scada_actor import ScadaActor

from named_types import GoDormant, WakeUp

class PumpDoctor(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 5

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False

    def start(self) -> None:
        ...
    
    def stop(self) -> None:
        ...
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case GoDormant():
                ...
            case WakeUp():
                ...
        return Ok(True)
