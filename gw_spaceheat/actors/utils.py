
# noinspection PyUnresolvedReferences
from proactor.mqtt import QOS
# noinspection PyUnresolvedReferences
from proactor.mqtt import Subscription
# noinspection PyUnresolvedReferences
from proactor import responsive_sleep

def gw_mqtt_topic_encode(candidate: str):
    return candidate.replace(".", "-")


def gw_mqtt_topic_decode(candidate: str):
    return candidate.replace("-", ".")


def dot_to_underscore(candidate):
    l = candidate.split(".")
    return "_".join(l)


def underscore_to_dot(candidate):
    l = candidate.split("_")
    return ".".join(l)




