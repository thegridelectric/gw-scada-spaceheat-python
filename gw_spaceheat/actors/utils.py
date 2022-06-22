import enum
import time
from typing import NamedTuple


class QOS(enum.Enum):
    AtMostOnce = 0
    AtLeastOnce = 1
    ExactlyOnce = 2


class Subscription(NamedTuple):
    Topic: str
    Qos: QOS

DEFAULT_STEP_DURATION = .1
def responsive_sleep(
        obj,
        seconds:float,
        step_duration:float = DEFAULT_STEP_DURATION,
        running_field_name: str = "_main_loop_running"
) -> bool:
    """Sleep in way that is more responsive to thread termination: sleep in step_duration increments up to
    specificed seconds, at after each step checking self._main_loop_running"""
    sleeps = int(seconds / step_duration)
    if sleeps * step_duration != seconds:
        last_sleep = seconds - (sleeps * step_duration)
    else:
        last_sleep = 0
    for _ in range(sleeps):
        if getattr(obj, running_field_name):
            time.sleep(step_duration)
    if getattr(obj, running_field_name) and last_sleep > 0:
        time.sleep(last_sleep)
    return getattr(obj, running_field_name)