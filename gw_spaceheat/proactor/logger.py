import logging
from typing import Optional, Any

import pendulum


class MessageSummary:
    """Helper class for formating message summaries message receipt/publication single line summaries."""

    DEFAULT_FORMAT = (
        "{timestamp}  {direction:4s}  {actor_alias:33s}  {broker_flag}  {arrow:2s}  {topic:80s}"
        "  {payload_type}"
    )

    @classmethod
    def format(
        cls,
        direction: str,
        actor_alias: str,
        topic: str,
        payload_object: Any = None,
        broker_flag=" ",
        timestamp: Optional[pendulum.datetime] = None,
    ) -> str:
        """
        Formats a single line summary of message receipt/publication.

        Args:
            direction: "IN" or "OUT"
            actor_alias: The node alias of the sending or receiving actor.
            topic: The destination or source topic.
            payload_object: The payload of the message.
            broker_flag: "*" for the "gw" broker.
            timestamp: "pendulum.now("UTC") by default.

        Returns:
            Formatted string.
        """
        try:
            if timestamp is None:
                timestamp = pendulum.now("UTC")
            direction = direction[:3].strip().upper()
            if direction in ["OUT", "SND"]:
                arrow = "->"
            elif direction.startswith("IN") or direction.startswith("RCV"):
                arrow = "<-"
            else:
                arrow = "? "
            if hasattr(payload_object, "payload"):
                payload_object = payload_object.payload
            if hasattr(payload_object, "__class__"):
                payload_str = payload_object.__class__.__name__
            else:
                payload_str = type(payload_object)
            return cls.DEFAULT_FORMAT.format(
                timestamp=timestamp.isoformat(),
                direction=direction,
                actor_alias=actor_alias,
                broker_flag=broker_flag,
                arrow=arrow,
                topic=f"[{topic}]",
                payload_type=payload_str,
            )
        except Exception as e:
            print(f"ouch got {e}")
            return ""


class ProactorLogger(logging.LoggerAdapter):

    message_summary_logger: logging.Logger
    lifecycle_logger: logging.Logger
    comm_event_logger: logging.Logger

    def __init__(self, base: str, message_summary: str, lifecycle: str, comm_event: str, extra: Optional[dict] = None):
        super().__init__(logging.getLogger(base), extra=extra)
        self.message_summary_logger = logging.getLogger(message_summary)
        self.lifecycle_logger = logging.getLogger(lifecycle)
        self.comm_event_logger = logging.getLogger(comm_event)

    @property
    def general_enabled(self) -> bool:
        return self.logger.isEnabledFor(logging.INFO)

    @property
    def message_summary_enabled(self) -> bool:
        return self.message_summary_logger.isEnabledFor(logging.INFO)

    @property
    def path_enabled(self) -> bool:
        return self.message_summary_logger.isEnabledFor(logging.DEBUG)

    @property
    def lifecycle_enabled(self) -> bool:
        return self.lifecycle_logger.isEnabledFor(logging.INFO)

    @property
    def comm_event_enabled(self) -> bool:
        return self.comm_event_logger.isEnabledFor(logging.INFO)

    def message_summary(
        self,
        direction: str,
        actor_alias: str,
        topic: str,
        payload_object: Any = None,
        broker_flag=" ",
        timestamp: Optional[pendulum.datetime] = None,
    ) -> None:
        if self.message_summary_logger.isEnabledFor(logging.INFO):
            self.message_summary_logger.info(
                MessageSummary.format(
                    direction=direction,
                    actor_alias=actor_alias,
                    topic=topic,
                    payload_object=payload_object,
                    broker_flag=broker_flag,
                    timestamp=timestamp
                )
            )

    def path(self, msg: str, *args, **kwargs) -> None:
        self.message_summary_logger.debug(msg, *args, **kwargs)

    def lifecycle(self, msg: str, *args, **kwargs) -> None:
        self.lifecycle_logger.info(msg, *args, **kwargs)

    def comm_event(self, msg: str, *args, **kwargs) -> None:
        self.comm_event_logger.info(msg, *args, **kwargs)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"{self.logger.name}, "
            f"{self.message_summary_logger.name}, "
            f"{self.lifecycle_logger.name}, "
            f"{self.comm_event_logger.name}>"
        )
