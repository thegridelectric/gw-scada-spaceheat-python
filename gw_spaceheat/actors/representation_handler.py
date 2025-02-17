"""Manages SCADA representation status for ATN interaction

This module handles the SCADA's representation status (Ready/Active/Dormant) according to
the SCADA-ATN representation protocol. It enforces the state transition rules and manages
the relationship between contract state and representation status.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import pytz

from gwproactor.logger import LoggerOrAdapter
from actors.config import ScadaSettings
from data_classes.house_0_layout import House0Layout
from enums import LogLevel, RepresentationStatus, ContractStatus
from gwproto.data_classes.sh_node import ShNode
from named_types import (
    Glitch, SetRepresentationStatus, SlowDispatchContract, SlowContractHeartbeat
)
from result import Err, Ok, Result

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
        self.contract_file = Path(f"{self.settings.paths.config_dir}/slow_dispatch_contract.json")
        self.status = RepresentationStatus.Dormant  # Start dormant until initialized
        self.hb: Optional[SlowContractHeartbeat] = None
        self.prev_contract: Optional[SlowDispatchContract] = None
        self._contract_end_time: Optional[datetime] = None

    @property 
    def status(self) -> RepresentationStatus:
        """Current representation status"""
        return self.status


    def load_contract_heartbeat(self) -> Optional[SlowContractHeartbeat]:
        """Loads existing SlowDispatchContract from persistent storage
        
        Load _hb if Terminated or Completed, else load hb.Contract 
        into _prev_contract
        """
        if not self.contract_file.exists(): # no file
            self.logger.info("No contract")
            return
        with open(self.contract_file, "r") as f:
            contract_data = json.load(f)
        ContractStatus.CompletedFailureByAtn
        try:
            hb = SlowContractHeartbeat.model_validate(contract_data)
            if hb.Status in [ContractStatus.TerminatedByAtn,
                             ContractStatus.TerminatedByScada,
                             ContractStatus.CompletedSuccess,
                             ContractStatus.CompletedFailureByAtn,
                             ContractStatus.CompletedFailureByScada
            ]:
                self.prev_contract = hb.Contract
            elif hb.Status in [ContractStatus.Received, ContractStatus.Confirmed, ContractStatus.Active]:
                self.hb = hb
            else:
                self.logger.warning(f"Unknown contract status {hb.Status}")
        except Exception as e:
            self.logger.warning(f"Issue loading contract! {e}")



    @property
    def prev_contract(self) -> Optional[SlowDispatchContract]:
        if self.hb:
            if not self.hb.is_live():
                self.prev_contract = self.hb
                self.hb = None

    def intialize(self) -> None:
        """Set initial status and contract state based on persistent store

        """
        now = datetime.now(self.timezone)
        if self.settings.representation_dormant:
            self.status = RepresentationStatus.Dormant
            self.logger.info("Starting in %s due to environment setting", self.status)
        else:
            if self.load_contract(): # live contract
                self.status = RepresentationStatus.Active
            elif self.in_grace_period(): # 
                self.status = Represe
            self.status = RepresentationStatus.Ready
            self.logger.info("Starting in %s state", self.status)

    def in_grace_period(self) -> bool:
        """ True if in an active contract"""
        if self.hb:
            return True
        elif not self.prev_contract:
            return False
        elif time.time() < self.prev_contract.ContractEndS + 60 * self.GRACE_PERIOD_MINUTES:
            return True
        else:
            return False

    def process_set_status(self, cmd: SetRepresentationStatus) -> Optional[Glitch]:
        """Handle SetRepresentationStatus command from ATN"""
        prior_status = self.status
        
        if cmd.Status == RepresentationStatus.Dormant:
            # Anyone can set dormant 
            self.status = RepresentationStatus.Dormant
        elif cmd.Status == RepresentationStatus.Ready:
            if self.status == RepresentationStatus.Dormant:
                # Only allow Ready from Dormant if no active contract
                if not self.hb:
                    self.status = RepresentationStatus.Ready
                else:
                    msg = "Cannot transition to Ready - active contract exists"
                    self.logger.warning(msg)
                    return self._make_glitch(msg, LogLevel.Warning)
            else:
                msg = f"Cannot set Ready from {self.status}"
                self.logger.warning(msg)
                return self._make_glitch(msg, LogLevel.Warning)
        # Note: Active status cannot be directly set, only via contract start
        
        if self.status != prior_status:
            msg = f"Status changed: {prior_status} -> {self.status}"
            if cmd.Reason:
                msg += f" Reason: {cmd.Reason}"
            self.logger.info(msg)
        return None

    def contract_started(self, starting_hb: SlowContractHeartbeat) -> None:
        """Called when a SlowDispatchContract is received
        
         - must have ContractStatusReceived

        """
        if self.status != RepresentationStatus.Ready:
            raise ValueError(
                f"Cannot start contract - SCADA not Ready (status: {self.status})"
            )
        if starting_hb.Status != ContractStatus.Received:
            raise ValueError(f"Call with a heartbeat with status Received, not {starting_hb.Status}")
        self.hb = starting_hb
        self.status = RepresentationStatus.Active
        
        # Calculate when contract will end
        start = datetime.fromtimestamp(contract.StartS, self.timezone)
        self._contract_end_time = start + timedelta(minutes=contract.DurationMinutes)
        
        self.logger.info(
            "Contract started - status now %s. Will end at %s",
            self.status,
            self._contract_end_time
        )

    def contract_ended(self) -> None:
        """Called when current dispatch contract ends"""
        if self.status != RepresentationStatus.Active:
            return  # Already handled or no active contract

        self.hb = None
        # Don't immediately go to Ready - wait for grace period
        # Status will be updated by check_state_transitions
        self.logger.info("Contract ended - waiting for grace period before Ready")

    def is_contract_live(self) -> bool:
        """Check if there is currently an active contract"""
        if not self.hb:
            return False
        return self.hb.is_live()
