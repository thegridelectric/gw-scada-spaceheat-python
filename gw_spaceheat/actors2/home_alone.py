from gwproto import Message
from result import Err
from result import Result

from actors2 import Actor


class HomeAlone(Actor):

    # container/members for any tasks started

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        # must at least be notified of changes in comm state
        return Err(ValueError(f"Unepected message type {type(message.Payload)}"))

    def start(self):
        # asyncio.create_task() any necessary tasks, storing the created task objects
        ...

    def stop(self):
        # cancel any running tasks
        ...

    async def join(self):
        # await any tasks
        ...

