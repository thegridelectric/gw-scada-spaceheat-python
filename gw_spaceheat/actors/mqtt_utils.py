import enum
from typing import NamedTuple


class QOS(enum.Enum):
    AtMostOnce = 0
    AtLeastOnce = 1
    ExactlyOnce = 2
    

class Subscription(NamedTuple):
    Topic: str
    Qos: QOS
