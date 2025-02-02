"""Type strat.boss.trigger version 000"""
from typing import Literal

from pydantic import BaseModel, model_validator
from enums import StratBossEvent, StratBossState

from typing_extensions import Self

class StratBossTrigger(BaseModel):
    """
    From strat-boss to its current boss: move into state StratBoss
    From current boss of strat-boss to strat-boss: command tree reflects the change
    """
    FromState: StratBossState
    ToState: StratBossState
    Trigger: StratBossEvent
    TypeName: Literal["strat.boss.trigger"] = "strat.boss.trigger"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: State machine consistency. Validate the triple belongs to
        transitions = [
            # Dormant -> Active triggers
            {"trigger": "HpTurnOnReceived", "source": "Dormant", "dest": "Active"},
            {"trigger": "DefrostDetected", "source": "Dormant", "dest": "Active"},
            # Active -> Dormant triggers
            {"trigger": "LiftDetected", "source": "Active", "dest": "Dormant"},
            {"trigger": "HpTurnOffReceived", "source": "Active", "dest": "Dormant"},
            {"trigger": "ActiveTwelveMinutes", "source": "Active", "dest": "Dormant"},
            {"trigger": "DistPumpSick", "source": "Active", "dest": "Dormant"},
        ]
        """

        return self

# TODO add axioms re consistency checking