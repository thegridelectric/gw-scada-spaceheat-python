import pytest
from schema.errors import MpSchemaError
from schema.gs.gs_pwr_maker import GsPwr_Maker as Maker


def test_gs_pwr():

    gw_tuple = Maker(power=3200).tuple

    assert Maker.tuple_to_type(gw_tuple) == b"\x80\x0c"
    assert Maker.type_to_tuple(b"\x80\x0c") == gw_tuple

    with pytest.raises(MpSchemaError):
        Maker(power="hi").tuple

    with pytest.raises(MpSchemaError):
        Maker(power=32768).tuple
