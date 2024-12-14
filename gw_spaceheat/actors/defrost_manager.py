import asyncio
import time
from typing import Sequence
from gwproactor import MonitoredName, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from result import Ok, Result
from actors.scada_actor import ScadaActor
from data_classes.house_0_names import H0CN

from named_types import GoDormant, WakeUp

class DefrostManager(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 5

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="")
        )

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, 120)]
    
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
        last_pat = time.time()
        while not self._stop_requested:

            self._send(PatInternalWatchdogMessage(src=self.name))