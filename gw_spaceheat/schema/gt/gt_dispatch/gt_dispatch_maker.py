"""Makes gt.dispatch type"""

import json
from typing import Dict, Optional


from schema.gt.gt_dispatch.gt_dispatch import GtDispatch
from schema.errors import MpSchemaError


class GtDispatch_Maker():
    type_alias = 'gt.dispatch.100'

    def __init__(self,
                    sh_node_alias: str,
                    relay_state: int):

        tuple = GtDispatch(ShNodeAlias=sh_node_alias,
                                            RelayState=relay_state,
                                            )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtDispatch) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtDispatch:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtDispatch:
        if "ShNodeAlias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ShNodeAlias")
        if "RelayState" not in d.keys():
            raise MpSchemaError(f"dict {d} missing RelayState")

        tuple = GtDispatch(ShNodeAlias=d["ShNodeAlias"],
                                            RelayState=d["RelayState"],
                                            )
        tuple.check_for_errors()
        return tuple
