"""Test HomeAlone actor"""

import pytest
from actors.home_alone import HomeAlone

import load_house
from config import ScadaSettings

from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus_Maker


def test_homealone_small():
    settings = ScadaSettings()
    layout = load_house.load_all(settings)
    with pytest.raises(Exception):
        HomeAlone(node=layout.node("a"), settings=settings, hardware_layout=layout)
    home_alone = HomeAlone(node=layout.node("a.home"), settings=settings, hardware_layout=layout)
    status_dict = {
        "SlotStartUnixS": 1656945300,
        "SimpleTelemetryList": [
            {
                "ValueList": [0, 1],
                "ReadTimeUnixMsList": [1656945400527, 1656945414270],
                "ShNodeAlias": "a.elt1.relay",
                "TypeAlias": "gt.sh.simple.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "5a71d4b3",
            }
        ],
        "AboutGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta",
        "BooleanactuatorCmdList": [
            {
                "ShNodeAlias": "a.elt1.relay",
                "RelayStateCommandList": [1],
                "CommandTimeUnixMsList": [1656945413464],
                "TypeAlias": "gt.sh.booleanactuator.cmd.status.100",
            }
        ],
        "FromGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta.scada",
        "MultipurposeTelemetryList": [
            {
                "AboutNodeAlias": "a.elt1",
                "ValueList": [18000],
                "ReadTimeUnixMsList": [1656945390152],
                "SensorNodeAlias": "a.m",
                "TypeAlias": "gt.sh.multipurpose.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "ad19e79c",
            }
        ],
        "FromGNodeId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "StatusUid": "dedc25c2-8276-4b25-abd6-f53edc79b62b",
        "ReportingPeriodS": 300,
        "TypeAlias": "gt.sh.status.110",
    }

    status_payload = GtShStatus_Maker.dict_to_tuple(status_dict)

    # Testing on_message

    # status_payload has to come from scada
    with pytest.raises(Exception):
        home_alone.on_message(from_node=layout.node("a.elt1"), payload=status_payload)

    home_alone.on_message(from_node=home_alone.scada_node(), payload=status_payload)
