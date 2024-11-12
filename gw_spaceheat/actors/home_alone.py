import asyncio
from gwproactor import  Actor, ServicesInterface
from result import Ok, Result
from gwproto import Message

class HomeAlone(Actor):
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
            self.services.logger.error(f"[{self.name}] In main loop. Sleeping for 5")
            await asyncio.sleep(5)


