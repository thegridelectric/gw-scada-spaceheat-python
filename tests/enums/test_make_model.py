"""Tests for schema enum spaceheat.make.model.000"""
from enums import MakeModel


def test_make_model() -> None:

    assert set(MakeModel.values()) == set(
        [
            "UNKNOWNMAKE__UNKNOWNMODEL",
            "EGAUGE__4030",
            "GRIDWORKS__SIMTSNAP1",
            "ATLAS__EZFLO",
            "MAGNELAB__SCT0300050",
            "YHDC__SCT013100",
            "NCD__PR814SPST",
            "ADAFRUIT__642",
            "GRIDWORKS__TSNAP1",
            "GRIDWORKS__WATERTEMPHIGHPRECISION",
            "GRIDWORKS__SIMPM1",
            "SCHNEIDERELECTRIC__IEM3455",
            "GRIDWORKS__SIMBOOL30AMPRELAY",
            "OPENENERGY__EMONPI",
        ]
    )

    assert MakeModel.default() == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL
