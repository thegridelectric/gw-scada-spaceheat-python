from gwproactor import ServicesInterface
import asyncio
from gwproto import Message
from result import Ok, Result
from actors.scada_actor import ScadaActor
from gwproto.named_types import ( GoDormant, WakeUp)

class AtomicAlly(ScadaActor):

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="AtomicAlly keepalive")
        )

    def stop(self) -> None:
        self._stop_requested = True
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case GoDormant():
                ...
            case WakeUp():
                ...
        return Ok(True)