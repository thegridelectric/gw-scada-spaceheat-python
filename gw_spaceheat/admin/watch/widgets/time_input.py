from textual.widgets import Input
from textual.validation import Number
from actors.config import AdminLinkSettings

class TimeInput(Input):
    def __init__(self, **kwargs):
        default_timeout_seconds = AdminLinkSettings().timeout_seconds
        default_value = int(default_timeout_seconds/60) if default_timeout_seconds else 5
        super().__init__(
            placeholder=f"Timeout minutes (default {default_value})",
            id="time_input",
            validators=[Number(minimum=1, maximum=24*60)],
            **kwargs
        )