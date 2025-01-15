"""Tests game.on type, version 000"""

from named_types import GameOn


def test_game_on_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "SendTimeMs": 1736811432571,
        "DispatchContractAddress": "bogus_algo_smart_contract_address",
        "Signature": "bogus_algo_signature",
        "TypeName": "game.on",
        "Version": "000",
    }

    d2 = GameOn.model_validate(d).model_dump(exclude_none=True)

    assert d2 == d
