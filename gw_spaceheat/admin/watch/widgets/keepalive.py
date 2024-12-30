import logging

from textual.logging import TextualHandler
from textual.message import Message
from textual.widgets import Button

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

    class Pressed(Message):
        ...

    def on_button_pressed(self) -> None:
        self.post_message(
            KeepAliveButton.Pressed()
        )


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
