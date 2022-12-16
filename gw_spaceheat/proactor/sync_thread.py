"""Classes providing interaction between synchronous and asynchronous code"""

import asyncio
import queue
import threading
import time
import traceback
from abc import ABC
from typing import Any
from typing import Optional

from actors.utils import responsive_sleep
from proactor.message import InternalShutdownMessage
from proactor.message import PatInternalWatchdogMessage


class AsyncQueueWriter:
    """Allow synchronous code to write to an asyncio Queue.

    It is assumed the asynchronous reader has access to the asyncio Queue "await get()" from directly from it.
    """

    _loop: Optional[asyncio.AbstractEventLoop] = None
    _async_queue: Optional[asyncio.Queue] = None

    def set_async_loop(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue) -> None:
        self._loop = loop
        self._async_queue = async_queue

    def put(self, item: Any) -> None:
        """Write to asyncio queue in a threadsafe way."""
        if self._loop is None or self._async_queue is None:
            raise ValueError("ERROR. start(loop, async_queue) must be called prior to put(item)")
        self._loop.call_soon_threadsafe(self._async_queue.put_nowait, item)


class SyncAsyncQueueWriter:
    """Provide a full duplex communication "channel" between synchronous and asynchronous code.

    It is assumed the asynchronous reader has access to the asyncio Queue "await get()" from directly from it.
    """

    _loop: Optional[asyncio.AbstractEventLoop] = None
    _async_queue: Optional[asyncio.Queue] = None
    sync_queue: Optional[queue.Queue]

    def __init__(self, sync_queue: Optional[queue.Queue] = None):
        self.sync_queue = sync_queue

    def set_async_loop(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue) -> None:
        self._loop = loop
        self._async_queue = async_queue

    def put_to_sync_queue(
        self, item: Any, block: bool = True, timeout: Optional[float] = None
    ):
        """Write to synchronous queue in a threadsafe way."""
        self.sync_queue.put(item, block=block, timeout=timeout)

    def put_to_async_queue(self, item: Any):
        """Write to asynchronous queue in a threadsafe way."""
        if self._loop is None or self._async_queue is None:
            raise ValueError("ERROR. start(loop, async_queue) must be called prior to put(item)")
        self._loop.call_soon_threadsafe(self._async_queue.put_nowait, item)

    def get_from_sync_queue(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> Any:
        """Read from synchronous queue in a threadsafe way."""
        return self.sync_queue.get(block=block, timeout=timeout)


class SyncAsyncInteractionThread(threading.Thread, ABC):
    """A thread wrapper providing an async-sync communication channel and simple "iterate, sleep, read message"
    semantics.
    """

    SLEEP_STEP_SECONDS = 0.01
    PAT_TIMEOUT = 20

    _channel: SyncAsyncQueueWriter
    running: Optional[bool]
    _iterate_sleep_seconds: Optional[float]
    _responsive_sleep_step_seconds: float
    pat_timeout: Optional[float]
    _last_pat_time: float

    def __init__(
        self,
        channel: Optional[SyncAsyncQueueWriter] = None,
        name: Optional[str] = None,
        iterate_sleep_seconds: Optional[float] = None,
        responsive_sleep_step_seconds: float = SLEEP_STEP_SECONDS,
        pat_timeout: Optional[float] = PAT_TIMEOUT,
        daemon: bool = True,
    ):
        super().__init__(name=name, daemon=daemon)
        if channel is None:
            self._channel = SyncAsyncQueueWriter()
        else:
            self._channel = channel
        self._iterate_sleep_seconds = iterate_sleep_seconds
        self._responsive_sleep_step_seconds = responsive_sleep_step_seconds
        self.running = None
        self.pat_timeout = pat_timeout
        self._last_pat_time = 0.0

    def _preiterate(self) -> None:
        pass

    def _iterate(self) -> None:
        pass

    def _handle_message(self, message: Any) -> None:
        pass

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def _handle_exception(self, exception: BaseException) -> bool:
        return False

    def request_stop(self) -> None:
        self.running = False

    def set_async_loop(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue) -> None:
        self._channel.set_async_loop(loop, async_queue)

    def set_async_loop_and_start(self, loop: asyncio.AbstractEventLoop, async_queue: asyncio.Queue) -> None:
        self.set_async_loop(loop, async_queue)
        self.start()

    def put_to_sync_queue(
        self, message: Any, block: bool = True, timeout: Optional[float] = None
    ) -> None:
        self._channel.put_to_sync_queue(message, block=block, timeout=timeout)

    def _put_to_async_queue(self, message: Any) -> None:
        self._channel.put_to_async_queue(message)

    def run(self):
        if self.running is None:
            self.running = True
            self._last_pat_time = time.time()
            self._preiterate()
            while self.running:
                try:
                    if self._iterate_sleep_seconds is not None:
                        responsive_sleep(
                            self,
                            self._iterate_sleep_seconds,
                            running_field_name="running",
                            step_duration=self._responsive_sleep_step_seconds,
                        )
                    if self.running:
                        self._iterate()
                    if self.running and self.time_to_pat():
                        self.pat_watchdog()
                    if self.running and self._channel.sync_queue is not None:
                        try:
                            message = self._channel.get_from_sync_queue(block=False)
                            if self.running:
                                self._handle_message(message)
                        except queue.Empty:
                            pass
                except BaseException as e:
                    handle_exception_str = ""
                    try:
                        handled = self._handle_exception(e)
                    except BaseException as e2:
                        handled = False
                        handle_exception_str = traceback.format_exception(e2)
                    if not handled:
                        self.running = False
                        reason = (
                            f"SyncAsyncInteractionThread ({self.name}) caught exception:\n"
                            f"{traceback.format_exception(e)}\n"
                        )
                        if handle_exception_str:
                            reason += (
                                "While handling that exception, _handle_exception caused exception:\n"
                                f"{handle_exception_str}\n"
                            )
                        self._put_to_async_queue(
                            InternalShutdownMessage(Src=self.name, Reason=reason)
                        )

    def time_to_pat(self) -> bool:
        return time.time() >= (self._last_pat_time + (self.pat_timeout / 2))

    def pat_watchdog(self):
        self._last_pat_time = time.time()
        self._put_to_async_queue(PatInternalWatchdogMessage(src=self.name))

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    async def async_join(self, timeout: float = None) -> None:
        # TODO: Giant hack. Alternate implementations below caused
        #       hangups or (probably) harmless but ugly exceptions
        await asyncio.sleep(0.1)

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
