from gwproactor import ServicesInterface
import asyncio
from gwproto import Message
from result import Ok, Result
from gwproto.named_types import ( GoDormant, WakeUp)
from actors.scada_actor import ScadaActor
class FakeAtn(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 61
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="FakeAtn keepalive")
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
    
    async def main(self):
        await asyncio.sleep(2)
        self.log("In synth gen main loop")
        while not self._stop_requested:
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)