import json
import random
import time
import datetime
import uuid
from pathlib import Path
from typing import Optional, Dict

import pytz
from gwproto.property_format import UUID4Str
from gwproto.data_classes.sh_node import ShNode
from data_classes.house_0_layout import House0Layout
from data_classes.house_0_names import H0N
from gwproactor.logger import LoggerOrAdapter

from enums import ContractStatus, RepresentationStatus, LogLevel
from named_types import (
    SlowContractHeartbeat, 
    SlowDispatchContract, 
    SetRepresentationStatus,
)
from enum import auto
from typing import List

from gw.enums import GwStrEnum

from tests.atn.atn_config import AtnSettings

class DispatchContractState(GwStrEnum):
    Expired = auto()
    

class AtnContractHandler:
    """Handles ATN's side of representation contract with SCADA and dispatch contracts"""

    DONE_STATES = [
        ContractStatus.TerminatedByAtn,
        ContractStatus.TerminatedByScada,
        ContractStatus.CompletedUnknownOutcome,
        ContractStatus.CompletedSuccess,
        ContractStatus.CompletedFailureByAtn,
        ContractStatus.CompletedFailureByScada,
    ]
    ACTIVE_STATES = [
        ContractStatus.Created,
        ContractStatus.Received,
        ContractStatus.Confirmed,
        ContractStatus.Active
    ]
    HEARTBEAT_INTERVAL_SECONDS = 60  # Send heartbeats once per minute
    LOGGER_NAME = "AtnContractHandler" 
    def __init__(
        self,
        node: ShNode,
        settings: AtnSettings,
        layout: House0Layout,
        logger: LoggerOrAdapter,
    ):
        self.settings = settings
        self.node = node
        self.layout = layout
        self.logger = logger
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.contract_file = Path(
            f"{self.settings.paths.data_dir}/atn_contract.json"
        )
        self.energy_used_wh: int = 0
        self.energy_updated_s: Optional[float] = None
        self.status: RepresentationStatus = RepresentationStatus.Active  # Default to active
        self.latest_hb: Optional[SlowContractHeartbeat] = None
        
    def load_heartbeat(self) -> Optional[SlowContractHeartbeat]:
        """Loads existing SlowContractHeartbeat from persistent storage
        
        - Returns None if no heartbeat exists
        - Otherwise loads the heartbeat and sets internal state
        """
        if not self.contract_file.exists():
            self.logger.info("No contract file found")
            return None
            
        with open(self.contract_file, "r") as f:
            contract_data = json.load(f)

        try:
            hb = SlowContractHeartbeat.model_validate(contract_data)
            
            # Store as latest heartbeat
            if hb.Status in self.DONE_STATES:
                # This is a completed contract, not active
                self.logger.info("Loaded completed contract")
                return None
        
            # Check if contract is still valid time-wise
            if time.time() > hb.Contract.contract_end_s():
                if hb.Status not in self.DONE_STATES:
                    # Contract has expired, need to mark as completed
                    self.logger.info("Loaded contract has expired, will send completion heartbeat")
                    self.latest_hb = hb
                    completion_hb = self.create_completion_heartbeat()
                    return completion_hb
                else:
                    return None
            else:
                self.logger.info(f"Loaded active contract: {self.formatted_contract(hb)}")
                self.energy_updated_s = hb.MessageCreatedMs / 1000
                if hb.FromNode == self.node.name:
                    if hb.Status != ContractStatus.Created:
                        raise Exception("Only save atn heartbeats with status Created!")
                    self.energy_used_wh = 0
                else:
                    if hb.WattHoursUsed is None:
                        raise Exception("hb from Scada must have WattHoursUsed!")
                    self.energy_used_wh = hb.WattHoursUsed
                self.latest_hb = hb
                return None
        except Exception as e:
            self.logger.error(f"Failed to load contract: {e}")
            return None
            
    def store_heartbeat(self, hb: Optional[SlowContractHeartbeat] = None) -> None:
        """Stores a SlowContractHeartbeat to persistent storage"""
        hb_to_store = self.latest_hb
        if hb:
            hb_to_store = hb
        if not hb_to_store: 
            raise Exception("Can't store hb if latest_hb is none!")
        
        if hb_to_store.FromNode == self.node.name:
            if hb_to_store not in [ContractStatus.Created, 
                                   ContractStatus.TerminatedByAtn,
                                   ContractStatus.CompletedUnknownOutcome]:
                raise Exception(f"Does not store atn hb with status {hb_to_store.Status}")
        
        with open(self.contract_file, "w") as f:
            f.write(hb_to_store.model_dump_json(indent=4))
    
    def initialize(self) -> Optional[SlowContractHeartbeat]:
        """Initialize contract handler state from persistent storage
        
        Returns a heartbeat if one needs to be sent to SCADA
        """
        hb = self.load_heartbeat()        
        return hb
    
    def create_new_contract(self, 
                           avg_power_watts: int, 
                           duration_minutes: int = 60, 
                           oil_boiler_on: bool = False) -> None:
        """Create a new dispatch contract
        
        This is called when the latest price is received and the ATN decides
        to create a new contract.
        """
        # Only create if there's no active contract or the active contract is done
        if self.latest_hb:
            raise Exception("Cannot create new contract while one is active")
            
        # Create contract starting at the next 5-minute boundary
        now = time.time()
        start_s = int(now - (now % 3600))

        contract = SlowDispatchContract(
            ScadaAlias=self.layout.scada_g_node_alias,
            StartS=start_s,
            DurationMinutes=duration_minutes,
            AvgPowerWatts=avg_power_watts,
            OilBoilerOn=oil_boiler_on,
            ContractId=str(uuid.uuid4()),
        )
        
        # Create initial heartbeat
        hb = SlowContractHeartbeat(
            FromNode=self.node.name,
            Contract=contract,
            Status=ContractStatus.Created,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=None,  # First message in chain
        )
        
        # Store heartbeat
        self.store_heartbeat()
        self.latest_hb = hb
    
    def create_termination_heartbeat(self, reason: str) -> SlowContractHeartbeat:
        """Create a heartbeat terminating the current contract"""
        if not self.latest_hb:
            raise Exception("No active contract to terminate")
            
        hb = SlowContractHeartbeat(
            FromNode=self.node.name,
            Contract=self.latest_hb.Contract,
            PreviousStatus=self.latest_hb.Status,
            Status=ContractStatus.TerminatedByAtn,
            Cause=reason,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_hb.MyDigit
        )
        
        # Store heartbeat
        self.store_heartbeat(hb)
        # Clear active contract
        self.latest_hb = None
        return hb
    
    def create_completion_heartbeat(self) -> SlowContractHeartbeat:
        """Create a heartbeat marking the current contract as completed

        Set latest_hb to None. Store the completion heartbeat
        """
        if not self.latest_hb:
            raise Exception("No active contract to terminate")
        if not time.time() > self.latest_hb.Contract.contract_end_s():
            raise Exception("Should not call this if contract time is not over!")
        hb = SlowContractHeartbeat(
            FromNode=self.node.name,
            Contract=self.latest_hb.Contract,
            PreviousStatus=self.latest_hb.Status,
            Status=ContractStatus.CompletedUnknownOutcome,
            Cause="Atn notes MarketSlot complete",
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_hb.MyDigit,
        )
        # Store
        self.store_heartbeat(hb)
        # Clear active contract
        self.latest_hb = None
        return hb
    
    def create_midcontract_heartbeat(self) -> SlowContractHeartbeat:
        """Generate the next heartbeat in the contract sequence
        
        Will raise an exception if latest_hb is None, if the time is past
        the latest_hb contract end, or if the status is Terminated
        """
        if self.latest_hb is None:
            raise Exception("Should not call this if latest_hb is None!")
        if time.time() > self.latest_hb.Contract.contract_end_s():
            raise Exception("Don't call this for an expired contract!")
        if self.latest_hb.Status == ContractStatus.Created:
            return self.latest_hb # haven't gotten the Received ack yet
        elif self.latest_hb.Status in [ContractStatus.Received, ContractStatus.Active]:
                return SlowContractHeartbeat(
                    FromNode=self.node.name,
                    Contract=self.latest_hb.Contract,
                    Status=ContractStatus.Active,
                    MessageCreatedMs=int(time.time() * 1000),
                    MyDigit=random.choice(range(10)),
                    YourLastDigit=self.latest_hb.MyDigit, 
                )
        else:
            raise Exception(f"Cannot call this if latest_hb.Status is {self.latest_hb.Status}")

    def process_slow_contract_heartbeat(self, scada_hb: SlowContractHeartbeat) -> None:
        """ - Does nothing if scada_hb does not match (latest_hb is None, mis-match in ContractId,
        or MessageCreatedMs is out of order)
        Otherwise:
          - sets self.latest_hb to this hb
          - updates energy_used_wh and energy_updated_s
          - stores the heartbeat
          - sets latest_hb to None if scada sends Completed or Terminated
          
        """
        if self.latest_hb is None:
            self.logger.info(f"Unexpected Scada hb ... we have no heartbeat! {scada_hb}")
            return
        if scada_hb.Contract.ContractId != self.latest_hb.Contract.ContractId:
            self.logger.info("Not the same ContractId ... ignoring")
            return
        if self.latest_hb is not None:
            if scada_hb.MessageCreatedMs < self.latest_hb.MessageCreatedMs:
                self.logger.info("hb received out of order. Ignoring!")
                return
        if scada_hb.WattHoursUsed is None: # also means FromNode is Scada
            raise Exception("this can't happen, axiomatically in Hb")
        
        self.energy_used_wh = scada_hb.WattHoursUsed
        self.energy_updated_s = time.time()
        self.store_heartbeat(scada_hb)
        if scada_hb.Status in [ContractStatus.TerminatedByScada,
                               ContractStatus.CompletedUnknownOutcome]:
            self.logger.info(f"Contract terminated by SCADA: {scada_hb.Cause}")
            self.latest_hb = None
        else:
            self.latest_hb = scada_hb

    def set_representation_status(self, status: RepresentationStatus, reason: str = "") -> SetRepresentationStatus:
        """Update the representation status and create a message to send to SCADA"""
        old_status = self.status
        self.status = status
        
        if old_status != status:
            self.logger.info(f"Representation status changed: {old_status} -> {status}")
            if reason:
                self.logger.info(f"Reason: {reason}")
                
        return SetRepresentationStatus(
            FromGNodeAlias=self.layout.atn_g_node_alias,
            TimeS=int(time.time()),
            Status=status,
            Reason=reason,
        )
        
    def formatted_contract(self, hb_to_format: Optional[SlowContractHeartbeat] = None) -> str:
        """Format contract heartbeat information for logging in a human-readable format."""
        hb = self.latest_hb
        if hb_to_format:
            hb = hb_to_format
        
        if not hb:
            return ""
        
        # Convert time to local timezone
        created_time = datetime.datetime.fromtimestamp(
            hb.MessageCreatedMs / 1000, 
            tz=self.timezone
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate total energy for the contract in Wh
        total_energy = hb.Contract.AvgPowerWatts * hb.Contract.DurationMinutes / 60
        
        # Energy used so far (only present in SCADA heartbeats)
        if hb.Status == ContractStatus.Created:
            energy_used = 0
        else:
            energy_used = f"{hb.WattHoursUsed} Wh" if hb.WattHoursUsed is not None else "Unknown"
        
        # Format the log string
        log_str = (
            f"Contract[{hb.Contract.ContractId[:8]}]: "
            f"{created_time} | "
            f"From: {hb.FromNode} | "
            f"Total: {total_energy:.1f} Wh | "
            f"Used: {energy_used} | "
            f"Status: {hb.Status.value}"
        )
        
        # Add reason if present
        if hb.Cause:
            log_str += f" | Reason: {hb.Cause}"
        
        return log_str

    def schedule_next_heartbeat(self) -> None:
        """Schedule the next heartbeat"""
        self.next_heartbeat_time = time.time() + self.HEARTBEAT_INTERVAL_SECONDS
    
    def is_heartbeat_due(self) -> bool:
        """Check if it's time to send a heartbeat"""
        return time.time() >= self.next_heartbeat_time
    