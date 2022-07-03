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
        "f8b497e8": MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION,
        "076da322": MakeModel.GRIDWORKS__SIMPM1,
        "d300635e": MakeModel.SCHNEIDERELECTRIC__IEM3455,
        "e81d74a8": MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY,
        "acd93fb3": MakeModel.ADAFRUIT__642,
        "fabfa505": MakeModel.NCD__PR814SPST,
        "b6a32d9b": MakeModel.UNKNOWNMAKE__UNKNOWNMODEL,
    }

    local_to_gt_dict: Dict[MakeModel, str] = {
        MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION: "f8b497e8",
        MakeModel.GRIDWORKS__SIMPM1: "076da322",
        MakeModel.SCHNEIDERELECTRIC__IEM3455: "d300635e",
        MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY: "e81d74a8",
        MakeModel.ADAFRUIT__642: "acd93fb3",
        MakeModel.NCD__PR814SPST: "fabfa505",
        MakeModel.UNKNOWNMAKE__UNKNOWNMODEL: "b6a32d9b",
        #
    }
