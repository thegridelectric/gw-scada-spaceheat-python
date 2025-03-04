"""Type pump.doc.trigger version 000"""
from typing import Literal

from pydantic import BaseModel, model_validator
from enums import PumpDocEvent, PumpDocState

from typing_extensions import Self

class PumpDocTrigger(BaseModel):
    """
    From pump-doc to its current boss: move into state PumpDoc
    From current boss of pump-doc to pump-doc: command tree reflects the change
    """
    FromState: PumpDocState
    ToState: PumpDocState
    Trigger: PumpDocEvent
    TypeName: Literal["pump.doc.trigger"] = "pump.doc.trigger"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: State machine consistency. Validate the triple belongs to
        transitions = [
            # Dormant -> Active triggers
            {"trigger": "NoDistFlow", "source": "Dormant", "dest": "Dist"},
            {"trigger": "NoPrimaryFlow", "source": "Dormant", "dest": "Primary"},
            {"trigger": "NoStoreFlow", "source": "Dormant", "dest": "Store}
            # Active -> Dormant triggers
            {"trigger": "Timeout", "source": "Dist/Primary/Store", "dest": "Dormant"},

        ]
        """

        return self

# TODO add axioms re consistency checking