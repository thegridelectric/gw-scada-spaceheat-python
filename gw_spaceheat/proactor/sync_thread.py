"""Classes providing interaction between synchronous and asynchronous code"""

import asyncio
import queue
import threading
from abc import ABC
from typing import Any, Optional

from actors.utils import responsive_sleep


class AsyncQueueWriter:
    """Allow synchronous code to write to an asyncio Queue.

    It is assumed the asynchronous reader has access to the asyncio Queue "await get()" from directly from it.
    """
    _loop: asyncio.AbstractEventLoop
    _async_queue: asyncio.Queue

    def __init__(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue):
        self._loop = loop
        self._async_queue = async_queue

    def put(self, item: Any) -> None:
        """Write to asyncio queue in a threadsafe way."""
        self._loop.call_soon_threadsafe(self._async_queue.put_nowait, item)


class SyncAsyncQueueWriter:
    """Provide a full duplex communication "channel" between synchronous and asynchronous code.

    It is assumed the asynchronous reader has access to the asyncio Queue "await get()" from directly from it.
    """
    _loop: asyncio.AbstractEventLoop
    _async_queue: asyncio.Queue
    sync_queue: Optional[queue.Queue]

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        async_queue: asyncio.Queue,
        sync_queue: Optional[queue.Queue] = None
    ):
        self._loop = loop
        self._async_queue = async_queue
        self.sync_queue = sync_queue

    def put_to_sync_queue(
        self, item: Any, block: bool = True, timeout: Optional[float] = None
    ):
        """Write to synchronous queue in a threadsafe way."""
        self.sync_queue.put(item, block=block, timeout=timeout)

    def put_to_async_queue(self, item: Any):
        """Write to asynchronous queue in a threadsafe way."""
        self._loop.call_soon_threadsafe(
            self._async_queue.put_nowait, item
        )

    def get_from_sync_queue(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Read from synchronous queue in a threadsafe way."""
        return self.sync_queue.get(block=block, timeout=timeout)


class SyncAsyncInteractionThread(threading.Thread, ABC):
    """A thread wrapper providing an async-sync communication channel and simple "iterate, sleep, read message"
    semantics.
    """
    SLEEP_STEP_SECONDS = .01

    _channel: SyncAsyncQueueWriter
    running: Optional[bool]
    _iterate_sleep_seconds: Optional[float]
    _responsive_sleep_step_seconds: float

    def __init__(
        self,
        channel: SyncAsyncQueueWriter,
        name: Optional[str] = None,
        iterate_sleep_seconds: Optional[float] = None,
        responsive_sleep_step_seconds=SLEEP_STEP_SECONDS,
        daemon: Optional[bool] = True,
    ):
        super().__init__(name=name, daemon=daemon)
        self._channel = channel
        self._iterate_sleep_seconds = iterate_sleep_seconds
        self._responsive_sleep_step_seconds = responsive_sleep_step_seconds
        self.running = None

    def _iterate(self) -> None:
        pass

    def _handle_message(self, message: Any) -> None:
        pass

    def request_stop(self) -> None:
        self.running = False

    def put_to_sync_queue(
        self, message: Any, block: bool = True, timeout: Optional[float] = None
    ) -> None:
        self._channel.put_to_sync_queue(message, block=block, timeout=timeout)

    def _put_to_async_queue(self, message: Any) -> None:
        self._channel.put_to_async_queue(message)

    def _get_from_sync_queue(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> Any:
        return self._channel.get_from_sync_queue(block=block, timeout=timeout)

    def run(self):
        if self.running is None:
            self.running = True
        while self.running:
            if self._iterate_sleep_seconds is not None:
                responsive_sleep(
                    self,
                    self._iterate_sleep_seconds,
                    running_field_name="running",
                    step_duration=self._responsive_sleep_step_seconds,
                )
            if self.running:
                self._iterate()
            if self.running and self._channel.sync_queue is not None:
                try:
                    message = self._channel.get_from_sync_queue(block=False)
                    if self.running:
                        self._handle_message(message)
                except queue.Empty:
                    pass

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    async def async_join(self, timeout: float = None) -> None:
        # TODO: Giant hack. Alternate implementations below caused
        #       hangups or (probably) harmless but ugly exceptions
        await asyncio.sleep(.1)

        # if timeout is not None:
        #     end = time.time() + timeout
        # else:
        #     end = None
        # if end is not None:
        #     remaining = end - time.time()
        # else:
        #     remaining = None
        # # harmless (?) exceptions
        # while (remaining is None or remaining > 0) and self.is_alive():
        #     await asyncio.sleep(.01)
        #     if remaining is not None:
        #         remaining = end - time.time()
        # # hangs
        # await asyncio.get_event_loop().run_in_executor(None, functools.partial(self.join, timeout=remaining))
