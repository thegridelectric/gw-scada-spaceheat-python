from typing import NamedTuple
from data_classes.sh_node import ShNode
from schema.enums import TelemetryName


class TelemetryTuple(NamedTuple):
    AboutNode: ShNode
    SensorNode: ShNode
    TelemetryName: TelemetryName

    def __repr__(self):
        return (
            f"TT({self.AboutNode.alias} {self.TelemetryName.value} read by {self.SensorNode.alias})"
        )
