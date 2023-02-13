from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.make_model.spaceheat_make_model_100 import (
    MakeModel,
    SpaceheatMakeModel100GtEnum,
)


class MakeModelGtEnum(SpaceheatMakeModel100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class MakeModelMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not MakeModelGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {MakeModelMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, make_model):
        if not isinstance(make_model, MakeModel):
            raise MpSchemaError(f"{make_model} must be of type {MakeModel}")
        return cls.local_to_gt_dict[make_model]

    gt_to_local_dict: Dict[str, MakeModel] = {
        "00000000": MakeModel.UNKNOWNMAKE__UNKNOWNMODEL,
        "beb6d3fb": MakeModel.EGAUGE__4030,
        "fabfa505": MakeModel.NCD__PR814SPST,
        "acd93fb3": MakeModel.ADAFRUIT__642,
        "d0178dc3": MakeModel.GRIDWORKS__TSNAP1,
        "f8b497e8": MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION,
        "076da322": MakeModel.GRIDWORKS__SIMPM1,
        "d300635e": MakeModel.SCHNEIDERELECTRIC__IEM3455,
        "e81d74a8": MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY,
        "c75d269f": MakeModel.OPENENERGY__EMONPI,
        "3042c432": MakeModel.GRIDWORKS__SIMTSNAP1,
        
        

        
    }

    local_to_gt_dict: Dict[MakeModel, str] = {
        MakeModel.UNKNOWNMAKE__UNKNOWNMODEL: "00000000",
        MakeModel.EGAUGE__4030: "beb6d3fb",
        MakeModel.NCD__PR814SPST: "fabfa505",
        MakeModel.ADAFRUIT__642: "acd93fb3",
        MakeModel.GRIDWORKS__TSNAP1: "d0178dc3",
        MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION: "f8b497e8",
        MakeModel.GRIDWORKS__SIMPM1: "076da322",
        MakeModel.SCHNEIDERELECTRIC__IEM3455: "d300635e",
        MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY: "e81d74a8",
        MakeModel.OPENENERGY__EMONPI: "c75d269f",
        MakeModel.GRIDWORKS__SIMTSNAP1: "3042c432",

        #
    }
