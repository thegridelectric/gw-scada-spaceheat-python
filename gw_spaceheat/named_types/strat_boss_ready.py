"""Type strat.boss.ready version 000"""
from typing import Literal

from pydantic import BaseModel


class StratBossReady(BaseModel):
    """
    Stratification boss is ready for heat pump primary pump to turn on
    """
    TypeName: Literal["strat.boss.ready"] = "strat.boss.ready"
    Version: Literal["000"] = "000"
