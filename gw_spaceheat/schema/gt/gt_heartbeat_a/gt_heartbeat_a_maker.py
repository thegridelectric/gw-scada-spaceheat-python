"""Makes gt.heartbeat.a type"""

import json
from typing import Dict, Optional


from schema.gt.gt_heartbeat_a.gt_heartbeat_a import GtHeartbeatA
from schema.errors import MpSchemaError


class GtHeartbeatA_Maker():
    type_alias = 'gt.heartbeat.a.100'

    def __init__(self):

        tuple = GtHeartbeatA()
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtHeartbeatA) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtHeartbeatA:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtHeartbeatA:

        tuple = GtHeartbeatA()
        tuple.check_for_errors()
        return tuple
