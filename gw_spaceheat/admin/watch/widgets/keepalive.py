import logging
from textual.logging import TextualHandler
from textual.message import Message
from textual.widgets import Button
from admin.watch.widgets.timer import TimerDigits
from admin.watch.widgets.time_input import TimeInput
from actors.config import AdminLinkSettings

module_logger = logging.getLogger(__name__)
module_logger.addHandler(TextualHandler())


class KeepAliveButton(Button):
    def __init__(
            self,
            logger: logging.Logger = module_logger,
            **kwargs
    ) -> None:
        super().__init__(
            "Keep alive",
            variant="primary",
            id="keepalive_button",
            **kwargs
        )
        self.logger = logger
        self.default_timeout_seconds = AdminLinkSettings().timeout_seconds
        self.default_timeout_seconds = self.default_timeout_seconds if self.default_timeout_seconds else 5*60
        self.timeout_seconds = self.default_timeout_seconds

    class Pressed(Message):
        def __init__(self, timeout_seconds):
            self.timeout_seconds = timeout_seconds
            super().__init__()

    def on_button_pressed(self) -> None:
        input_value = self.app.query_one(TimeInput).value
        try:
            time_in_minutes = float(input_value) if input_value else int(self.default_timeout_seconds/60)
            self.timeout_seconds = int(time_in_minutes * 60)
        except ValueError:
            print(f"Invalid input: '{input_value}', please enter a valid number.")
        self.post_message(KeepAliveButton.Pressed(self.timeout_seconds))
        timer_display = self.app.query_one(TimerDigits)
        timer_display.restart(self.timeout_seconds)


class ReleaseControlButton(Button):
    def __init__(
            self,
            logger: logging.Logger = module_logger,
            **kwargs
    ) -> None:
        super().__init__(
            "Release control",
            variant="primary",
            id="release_control_button",
            **kwargs
        )
        self.logger = logger

    class Pressed(Message):
        ...

    def on_button_pressed(self) -> None:
        self.post_message(
            ReleaseControlButton.Pressed()
        )
