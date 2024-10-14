from pydantic import BaseModel


class BaseReading(BaseModel):
    string: str = ""

    def __str__(self):
        return self.string

    def __bool__(self) -> bool:
        return False

class MissingReading(BaseReading): ...

class Reading(BaseReading):
    raw: int
    converted: float | int
    report_time_unix_ms: int
    idx: int

    def __bool__(self) -> bool:
        return True
