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
                    completion_hb = self.create_completion_heartbeat(hb)
                    return completion_hb
                else:
                    return None
            else:
                self.logger.info(f"Loaded active contract: {self.format_contract_log(hb)}")
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
            
    def store_heartbeat(self) -> None:
        """Stores a SlowContractHeartbeat to persistent storage"""
        if not self.latest_hb: 
            raise Exception("Can't store hb if latest_hb is none!")
        
        if self.latest_hb.FromNode == self.node.name:
            if self.latest_hb != ContractStatus.Created:
                raise Exception(f"Only store latest hb genearted by atn if status is Created! {self.latest_hb}")
        
        with open(self.contract_file, "w") as f:
            f.write(self.latest_hb.model_dump_json(indent=4))
    
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
        start_s = int(now - (now % 300) + 300)  # Next 5-minute boundary
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
    
    def create_termination_heartbeat(self, reason: str) -> Optional[SlowContractHeartbeat]:
        """Create a heartbeat terminating the current contract"""
        if not self.active_contract_id or not self.latest_hb:
            self.logger.warning("No active contract to terminate")
            return None
            
        hb = SlowContractHeartbeat(
            FromNode=self.node.name,
            Contract=self.latest_hb.Contract,
            PreviousStatus=self.latest_hb.Status,
            Status=ContractStatus.TerminatedByAtn,
            Cause=reason,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_scada_hb.MyDigit if self.latest_scada_hb else None,
        )
        
        # Store heartbeat
        self.store_heartbeat(hb)
        
        # Clear active contract
        self.active_contract_id = None
        
        return hb
    
    def create_completion_heartbeat(self, previous_hb: SlowContractHeartbeat) -> SlowContractHeartbeat:
        """Create a heartbeat marking the current contract as completed"""
        hb = SlowContractHeartbeat(
            FromNode=self.node.name,
            Contract=previous_hb.Contract,
            PreviousStatus=previous_hb.Status,
            Status=ContractStatus.CompletedUnknownOutcome,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_scada_hb.MyDigit if self.latest_scada_hb else None,
        )
        
        # Store heartbeat
        self.store_heartbeat(hb)
        
        # Clear active contract
        self.active_contract_id = None
        
        return hb
    
    def generate_next_heartbeat(self) -> Optional[SlowContractHeartbeat]:
        """Generate the next heartbeat in the contract sequence
        
        This is called periodically to maintain the contract heartbeat
        """
        if not self.active_contract_id:
            self.schedule_next_heartbeat()
            return None
            
        # If we don't have a scada response yet but have sent a contract, check if we need to resend
        if not self.latest_scada_hb and self.latest_hb and self.latest_hb.Status == ContractStatus.Created:
            # Check if it's been over 30 seconds since we sent the contract
            last_sent_time = self.latest_hb.MessageCreatedMs / 1000
            if time.time() - last_sent_time > 30:
                # Resend the contract creation
                hb = SlowContractHeartbeat(
                    FromNode=self.node.name,
                    Contract=self.latest_hb.Contract,
                    Status=ContractStatus.Created,
                    MessageCreatedMs=int(time.time() * 1000),
                    MyDigit=random.choice(range(10)),
                    YourLastDigit=None,  # Still first message
                )
                self.store_heartbeat()
                self.schedule_next_heartbeat()
                return hb
                
        # If we have received a response from SCADA
        if self.latest_scada_hb:
            # Check the status of the contract
            if self.latest_scada_hb.Status == ContractStatus.Received:
                # SCADA has received, we should confirm
                hb = SlowContractHeartbeat(
                    FromNode=self.node.name,
                    Contract=self.latest_scada_hb.Contract,
                    PreviousStatus=self.latest_scada_hb.Status,
                    Status=ContractStatus.Confirmed,
                    MessageCreatedMs=int(time.time() * 1000),
                    MyDigit=random.choice(range(10)),
                    YourLastDigit=self.latest_scada_hb.MyDigit,
                )
                self.store_heartbeat(hb)
                self.schedule_next_heartbeat()
                return hb
                
            elif self.latest_scada_hb.Status == ContractStatus.Active:
                # Contract is active, send periodic active updates
                # ATN is not authoritative about "Active" status
                hb = SlowContractHeartbeat(
                    FromNode=self.node.name,
                    Contract=self.latest_scada_hb.Contract,
                    Status=ContractStatus.Active,
                    MessageCreatedMs=int(time.time() * 1000),
                    MyDigit=random.choice(range(10)),
                    YourLastDigit=self.latest_scada_hb.MyDigit,
                    IsAuthoritative=False,
                )
                self.store_heartbeat(hb)
                self.schedule_next_heartbeat()
                return hb
                
            elif self.latest_scada_hb.Status in self.DONE_STATES:
                # Contract is done, clear active contract
                self.active_contract_id = None
                # Send one final acknowledgment
                hb = SlowContractHeartbeat(
                    FromNode=self.node.name,
                    Contract=self.latest_scada_hb.Contract,
                    Status=self.latest_scada_hb.Status,
                    MessageCreatedMs=int(time.time() * 1000),
                    MyDigit=random.choice(range(10)),
                    YourLastDigit=self.latest_scada_hb.MyDigit,
                    IsAuthoritative=False,
                )
                self.store_heartbeat(hb)
                return hb
                
        self.schedule_next_heartbeat()
        return None
    
    def process_heartbeat(self, hb: SlowContractHeartbeat) -> Optional[SlowContractHeartbeat]:
        """Process a heartbeat from SCADA
        
        Returns a response heartbeat if one should be sent
        """
        # Validate heartbeat is from SCADA
        if hb.FromNode != H0N.primary_scada:
            self.logger.warning(f"Received heartbeat from {hb.FromNode}, not SCADA")
            return None
            
        if self.latest_hb is None:
            self.logger.info("Got heartbeat when we have no live contract ... ignoring")
            return
        if self.latest_hb.Contract.ContractId != hb.Contract.ContractId:
            self.logger.info(f"Got hb for different contract. ignoring. mine: {self.latest_hb}."
                             f"Inbound: {hb}")
        
        # check if contract has expired. If so
        # If we get to here it means the hb is for our live contract. Make sure its the latest
        # we'vce received from Scada before storing it
        if self.latest_hb is not None:
            if hb.MessageCreatedMs < self.latest_scada_hb.MessageCreatedMs:
                self.logger.info("hb receivced out of order. Ignoring!")
        self.latest_scada_hb = hb
        self.store_heartbeat()

        # Check the status
        if hb.Status == ContractStatus.Received:
            # SCADA has received our contract, respond with confirmation
            response = SlowContractHeartbeat(
                FromNode=self.node.name,
                Contract=hb.Contract,
                PreviousStatus=hb.Status,
                Status=ContractStatus.Confirmed,
                MessageCreatedMs=int(time.time() * 1000),
                MyDigit=random.choice(range(10)),
                YourLastDigit=hb.MyDigit,
            )
            # Reset next heartbeat time to maintain regular frequency
            self.schedule_next_heartbeat()
            return response
            
        elif hb.Status == ContractStatus.TerminatedByScada:
            # SCADA has terminated the contract
            self.logger.info(f"Contract terminated by SCADA: {hb.Cause}")
            # Clear active contract if this is our active one
            if self.active_contract_id == hb.Contract.ContractId:
                self.active_contract_id = None
            # Send acknowledgment
            response = SlowContractHeartbeat(
                FromNode=self.node.name,
                Contract=hb.Contract,
                Status=ContractStatus.TerminatedByScada,
                MessageCreatedMs=int(time.time() * 1000),
                MyDigit=random.choice(range(10)),
                YourLastDigit=hb.MyDigit,
                IsAuthoritative=False,
            )
            self.store_heartbeat(response)
            return response
            
        elif hb.Status == ContractStatus.CompletedUnknownOutcome:
            # Contract has completed
            self.logger.info("Contract completed")
            # Clear active contract if this is our active one
            if self.active_contract_id == hb.Contract.ContractId:
                self.active_contract_id = None
            # Send acknowledgment
            response = SlowContractHeartbeat(
                FromNode=self.node.name,
                Contract=hb.Contract,
                Status=ContractStatus.CompletedUnknownOutcome,
                MessageCreatedMs=int(time.time() * 1000),
                MyDigit=random.choice(range(10)),
                YourLastDigit=hb.MyDigit,
                IsAuthoritative=False,
            )
            self.store_heartbeat(response)
            return response
            
        # For other statuses, just store the heartbeat but don't respond directly
        self.store_heartbeat(hb)
        return None

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
        
    def has_active_contract(self) -> bool:
        """Check if there is an active contract"""
        return (
            self.active_contract_id is not None and 
            self.latest_hb is not None and
            self.latest_hb.Status in self.ACTIVE_STATES
        )
        
    def can_create_new_contract(self) -> bool:
        """Check if a new contract can be created"""
        # Cannot create if representation is dormant
        if self.status == RepresentationStatus.Dormant:
            return False
            
        # Cannot create if there's an active contract
        if self.has_active_contract():
            return False
            
        return True

    def format_contract_log(self, hb: SlowContractHeartbeat) -> str:
        """Format contract heartbeat information for logging in a human-readable format."""
        if not hb:
            return "No contract"
        
        # Convert time to local timezone
        created_time = datetime.datetime.fromtimestamp(
            hb.MessageCreatedMs / 1000, 
            tz=self.timezone
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate total energy for the contract in Wh
        total_energy = hb.Contract.AvgPowerWatts * hb.Contract.DurationMinutes / 60
        
        # Energy used so far (only present in SCADA heartbeats)
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
    