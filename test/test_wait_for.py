import asyncio
from typing import Optional

import pytest
import time

from test.test_actor_utils import StopWatch
from test.utils import wait_for, await_for, AwaitablePredicate


class Delay:
    until: float
    result: bool
    sleep_duration: Optional[float]

    def __init__(self, delay: float, result: bool = True, duration: Optional[float] = None):
        self.result = result
        self.sleep_duration = duration
        self.restart(delay)

    def restart(self, delay: float):
        self.until = time.time() + delay

    def __call__(self):
        if self.sleep_duration is not None:
            time.sleep(self.sleep_duration)
        if time.time() >= self.until:
            return self.result
        else:
            return False


def async_delay(delay: Delay) -> AwaitablePredicate:

    async def async_function():
        if delay.sleep_duration is not None:
            await asyncio.sleep(delay.sleep_duration)
        if time.time() >= delay.until:
            return delay.result
        else:
            return False

    return async_function


def test_wait_for():

    delay_time = .01
    timeout = delay_time * 2
    retry_duration = delay_time / 4
    sw = StopWatch()

    # Happy path
    with sw:
        wait_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time
    assert sw.elapsed < delay_time + (2 * retry_duration)
    assert sw.elapsed < timeout

    # Timeout immediately passed, run f() at least once.
    delay_time = 0
    timeout = 0
    retry_duration = .01
    with sw:
        wait_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time

    # Call itself is too long, but returns True immediately
    delay_time = 0
    timeout = .1
    duration = timeout * 2
    retry_duration = .01
    with sw:
        wait_for(Delay(delay_time, duration=duration), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= duration
    assert sw.elapsed > timeout

    # Timeout exceeded
    with pytest.raises(ValueError):
        wait_for(Delay(1), .01)

    # Timeout exceeded, return result rather than raising exception
    assert wait_for(Delay(1), .01, raise_timeout=False) is False

    # Retry_duration is used
    delay_time = .01
    timeout = 1
    retry_duration = .1
    with sw:
        wait_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= retry_duration
    assert sw.elapsed < retry_duration * 2
    assert sw.elapsed < timeout


@pytest.mark.asyncio
async def test_await_for():

    delay_time = .01
    timeout = delay_time * 2
    retry_duration = delay_time / 4
    min_expected = delay_time + (2 * retry_duration)
    sw = StopWatch()

    # Happy path
    with sw:
        await await_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time
    assert sw.elapsed < min_expected
    assert sw.elapsed < timeout

    # Timeout immediately passed, run f() at least once.
    delay_time = 0
    timeout = 0
    retry_duration = .01
    with sw:
        await await_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time

    # Call itself is too long, but returns True immediately
    delay_time = 0
    timeout = .1
    duration = timeout * 2
    retry_duration = .01
    with sw:
        await await_for(Delay(delay_time, duration=duration), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= duration
    assert sw.elapsed > timeout

    # Timeout exceeded
    with pytest.raises(ValueError):
        await await_for(Delay(1), .01)

    # Timeout exceeded, return result rather than raising exception
    assert await await_for(Delay(1, True), .01, raise_timeout=False) is False

    # Retry_duration is used
    delay_time = .01
    timeout = 1
    retry_duration = .1
    with sw:
        await await_for(Delay(delay_time), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= retry_duration
    assert sw.elapsed < retry_duration * 2
    assert sw.elapsed < timeout

    # Function f is a coroutine, happy path
    delay_time = .01
    timeout = delay_time * 2
    retry_duration = delay_time / 4
    min_expected = delay_time + (2 * retry_duration)
    with sw:
        await await_for(async_delay(Delay(delay_time)), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time
    assert sw.elapsed < min_expected
    assert sw.elapsed < timeout

    # Function f is a coroutine, Timeout immediately passed, await f() at least once.
    delay_time = 0
    timeout = 0
    retry_duration = .01
    with sw:
        await await_for(async_delay(Delay(delay_time)), timeout, retry_duration=retry_duration)
    assert sw.elapsed >= delay_time
