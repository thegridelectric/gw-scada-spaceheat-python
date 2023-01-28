from typing import Generic
from typing import Optional
from typing import TypeVar

R = TypeVar("R", covariant=True)  # Result type

class DriverResult(Generic[R]):
    """A class which allows limited interface drivers any warnings that accumulated on the way to getting an actual result."""
    value: R
    warnings: list[Exception]

    def __init__(self, value: R, warnings: Optional[list[Exception]] = None):
        self.value = value
        if warnings is None:
            self.warnings = []
        else:
            self.warnings = warnings[:]
