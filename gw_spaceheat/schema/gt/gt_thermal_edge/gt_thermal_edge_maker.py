"""Makes gt.thermal.edge type"""

import json
from typing import Dict, Optional
from data_classes.thermal_edge import ThermalEdge

from schema.gt.gt_thermal_edge.gt_thermal_edge import GtThermalEdge
from schema.errors import MpSchemaError


class GtThermalEdge_Maker():
    type_alias = 'gt.thermal.edge.100'

    def __init__(self,
                 thermal_edge_id: str):

        tuple = GtThermalEdge(ThermalEdgeId=thermal_edge_id,
                                          )
        tuple.check_for_errors()
        self.tuple: GtThermalEdge = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtThermalEdge) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtThermalEdge:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtThermalEdge:
        if "ThermalEdgeId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ThermalEdgeId")

        tuple = GtThermalEdge(ThermalEdgeId=d["ThermalEdgeId"],                                        
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtThermalEdge) -> ThermalEdge:
        s = {
            'thermal_edge_id': t.ThermalEdgeId,
            }
        if s['thermal_edge_id'] in ThermalEdge.by_id.keys():
            dc = ThermalEdge.by_id[s['thermal_edge_id']]
        else:
            dc = ThermalEdge(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ThermalEdge) -> GtThermalEdge:
        if dc is None:
            return None
        t = GtThermalEdge(
            sThermalEdgeId=dc.thermal_edge_id,
                                            )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ThermalEdge:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ThermalEdge) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ThermalEdge:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
