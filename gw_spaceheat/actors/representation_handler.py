"""Manages SCADA representation status for ATN interaction

This module handles the SCADA's representation status (Ready/Active/Dormant) according to
the SCADA-ATN representation protocol. It enforces the state transition rules and manages
the relationship between contract state and representation status.
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
import pytz

from gwproactor.logger import LoggerOrAdapter
from actors.config import ScadaSettings
from data_classes.house_0_layout import House0Layout
from enums import LogLevel, RepresentationStatus 
from gwproto.data_classes.sh_node import ShNode
from named_types import (
    SetRepresentationStatus, SlowDispatchContract, Glitch
)


class RepresentationHandler:
    """Handles SCADA's representation status and related state transitions"""

    GRACE_PERIOD_MINUTES = 5  # Time after contract end before auto-ready
    LOGGER_NAME = "RepresentationHandler"

    def __init__(
        self,
        settings: ScadaSettings,
        layout: House0Layout,
        node: ShNode,
        logger: LoggerOrAdapter
    ):
        self.settings = settings
        self.layout = layout
        self.node = node
        self.timezone =  pytz.timezone(self.settings.timezone_str)

        self.logger = logger
        self._status = RepresentationStatus.Dormant  # Start dormant until initialized
        self._active_contract: Optional[SlowDispatchContract] = None
        self._contract_end_time: Optional[datetime] = None
        self._stop_requested = False

    @property 
    def status(self) -> RepresentationStatus:
        """Current representation status"""
        return self._status

    def initialize_from_env(self) -> SetRepresentationStatus:
        """Set initial status based on environment variables"""
        if self.settings.representation_dormant:
            self._status = RepresentationStatus.Dormant
            self.logger.info("Starting in %s due to environment setting", self._status)
            return SetRepresentationStatus(
                Status=RepresentationStatus.Dormant,
                Reason="Scada just rebooted; initializing from env file"
            )
        else:
            self._status = RepresentationStatus.Ready
            self.logger.info("Starting in %s state", self._status)
            return SetRepresentationStatus(
                Status=RepresentationStatus.Ready,
                Reason="Scada just rebooted; initializing from env file"
            )

    def process_set_status(self, cmd: SetRepresentationStatus) -> Optional[Glitch]:
        """Handle SetRepresentationStatus command from ATN"""
        prior_status = self._status
        
        if cmd.Status == RepresentationStatus.Dormant:
            # Anyone can set dormant 
            self._status = RepresentationStatus.Dormant
        elif cmd.Status == RepresentationStatus.Ready:
            if self._status == RepresentationStatus.Dormant:
                # Only allow Ready from Dormant if no active contract
                if not self._active_contract:
                    self._status = RepresentationStatus.Ready
                else:
                    msg = "Cannot transition to Ready - active contract exists"
                    self.logger.warning(msg)
                    return self._make_glitch(msg, LogLevel.Warning)
            else:
                msg = f"Cannot set Ready from {self._status}"
                self.logger.warning(msg)
                return self._make_glitch(msg, LogLevel.Warning)
        # Note: Active status cannot be directly set, only via contract start
        
        if self._status != prior_status:
            msg = f"Status changed: {prior_status} -> {self._status}"
            if cmd.Reason:
                msg += f" Reason: {cmd.Reason}"
            self.logger.info(msg)
        return None

    def contract_started(self, contract: SlowDispatchContract) -> None:
        """Called when a dispatch contract becomes active"""
        if self._status != RepresentationStatus.Ready:
            raise ValueError(
                f"Cannot start contract - SCADA not Ready (status: {self._status})"
            )
        
        self._active_contract = contract
        self._status = RepresentationStatus.Active
        
        # Calculate when contract will end
        start = datetime.fromtimestamp(contract.StartS, self.timezone)
        self._contract_end_time = start + timedelta(minutes=contract.DurationMinutes)
        
        self.logger.info(
            "Contract started - status now %s. Will end at %s",
            self._status,
            self._contract_end_time
        )

    def contract_ended(self) -> None:
        """Called when current dispatch contract ends"""
        if self._status != RepresentationStatus.Active:
            return  # Already handled or no active contract

        self._active_contract = None
        # Don't immediately go to Ready - wait for grace period
        # Status will be updated by check_state_transitions
        self.logger.info("Contract ended - waiting for grace period before Ready")

    async def check_state_transitions(self) -> None:
        """Periodic check for status transitions
        
        Main transition checked is Active -> Ready after grace period
        """
        while not self._stop_requested:
            try:
                now = datetime.now(self.timezone)
                
                if (self._status == RepresentationStatus.Active and
                    self._contract_end_time and 
                    now > self._contract_end_time + timedelta(minutes=self.GRACE_PERIOD_MINUTES)):
                    # Grace period after contract ended - go to Ready
                    self._status = RepresentationStatus.Ready
                    self._contract_end_time = None
                    self.logger.info("Grace period completed - status now %s", self._status)

                await asyncio.sleep(60)  # Check every minute
            
            except Exception as e:
                self.logger.error("Error in transition checker: %s", e)
                await asyncio.sleep(60)  # Sleep even on error

    def stop(self) -> None:
        """Stop the transition checker task"""
        self._stop_requested = True

    def is_contract_live(self) -> bool:
        """Check if there is currently an active contract"""
        if not self._active_contract:
            return False
        return self._active_contract.is_live()

    def _make_glitch(self, msg: str, level: LogLevel) -> Glitch:
        """Helper to create consistently formatted Glitch messages"""
        return Glitch(
            FromGNodeAlias=self.layout.scada_g_node_alias,
            Node=self.node.name,
            Type=level,
            Summary=self.LOGGER_NAME,
            Details=msg,
        )