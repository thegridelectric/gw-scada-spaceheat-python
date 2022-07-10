"""Test actors.utils module"""

import threading
import time

from actors.utils import responsive_sleep


class StopWatch(object):
    """Measure time with context manager"""

    start: float = 0
    end: float = 0
    elapsed: float = 0

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type_, value, traceback):
        self.end = time.time()
        self.elapsed = self.end - self.start


class StopMe:
    def __init__(self, running: bool = True, step_duration: float = 0.1):
        self.running = running
        self.step_duration = step_duration
        self.thread = threading.Thread(target=self.loop)

    def loop(self):
        while self.running:
            print(".")
            responsive_sleep(
                self, 1.0, step_duration=self.step_duration, running_field_name="running"
            )

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()


MAX_DELAY = 0.01


def test_responsive_sleep():
    sw = StopWatch()
    seconds = 0.1
    with sw:
        responsive_sleep(StopMe(), seconds, running_field_name="running")
    assert seconds <= sw.elapsed < seconds + MAX_DELAY
    seconds = 0.01
    with sw:
        responsive_sleep(StopMe(), seconds, running_field_name="running")
    assert seconds <= sw.elapsed < seconds + MAX_DELAY
    with sw:
        responsive_sleep(StopMe(running=False), seconds, running_field_name="running")
    assert 0 <= sw.elapsed < MAX_DELAY
    step_duration = 0.1
    stop_me = StopMe(step_duration=step_duration)
    stop_me.start()
    with sw:
        stop_me.stop()
    assert 0 <= sw.elapsed < step_duration + MAX_DELAY
