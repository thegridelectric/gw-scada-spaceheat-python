import json
import uuid
import time
import asyncio
from dataclasses import dataclass
from pathlib import Path
from gw.data_classes.market_type import MarketType, Rt60Gate5
from typing import Dict, List, Optional
from gwproto import Message
from gwproto.property_format import MarketSlotName
from gwproactor import ServicesInterface
from actors.scada_actor import ScadaActor
from gw.enums import MarketTypeName
from named_types import DispatchContract, EnergyInstruction, MarketMakerAck
from result import Err, Ok, Result


class MarketSlotContracts:
    """Manages all contracts for a specific market slot"""
    def __init__(self, market_slot_name: MarketSlotName):
        self.market_slot_name = market_slot_name
        self.contracts: Dict[str, DispatchContract] = {}
        self._aggregated: Optional[DispatchContract] = None
        
    def add_contract(self, contract: DispatchContract) -> None:
        """Add a new contract to this market slot"""
        if contract.MarketSlotName != self.market_slot_name:
            raise ValueError(f"Contract for wrong market slot {contract.MarketSlotName}")
        self.contracts[contract.ContractId] = contract
        self._aggregated = None  # Clear cached aggregation

    def all_contracts_acked(self) -> bool:
       validated_contracts = [c for c in self.contracts.values() 
                             if c.ValidatedByMarketMaker]
       if len(validated_contracts) == len(list(self.contracts.values())):
           return True
       return False

    def get_aggregated_contract(self) -> Optional[DispatchContract]:
        """Get the aggregated contract for this market slot.
        Only includes validated contracts."""
        if self._aggregated is not None:
            return self._aggregated
            
        validated_contracts = [c for c in self.contracts.values() 
                             if c.ValidatedByMarketMaker]

        if not validated_contracts:
            return None

        # Simple aggregation - sum the power
        total_power = sum(c.AvgPowerWatts for c in validated_contracts)
        sample = validated_contracts[0]
        self._aggregated = DispatchContract(
            ContractId=str(uuid.uuid4()),
            MarketSlotName=self.market_slot_name,
            BidderAlias=sample.BidderAlias,
            StartUnixS=sample.StartUnixS,
            DurationMinutes=sample.DurationMinutes,
            AvgPowerWatts=total_power,
            Status="Active" if any(c.Status == "Active" for c in validated_contracts) else "Pending",
            ValidatedByMarketMaker=True
        )
        return self._aggregated

@dataclass
class ActiveMarkets:
    """Tracks active markets by type and their contracts"""
    market_type: MarketType
    active_slots: Dict[MarketSlotName, MarketSlotContracts]

class ContractManager(ScadaActor):
    """Manages dispatch contracts across different market types"""
    
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        # Start with just Rt60Gate5 for hw1.isone.
        self.market_maker_alias =  "hw1.isone.me.versant.keene"
        self.supported_markets = {
            Rt60Gate5: ActiveMarkets(
                market_type=Rt60Gate5,
                active_slots={}
            )
        }
        self.contract_file = self.settings.paths.config_dir / "dispatch_contracts.json"

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(
                self.defrost_watcher(), name="defrost_watcher"
            )
        )

    def stop(self) -> None:
        """ Required method, used for stopping tasks. Noop"""
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...
    def load_contracts(self) -> Result[List[DispatchContract], Exception]:
        """Load contracts from persistent storage.
        
        Returns Ok(contracts) if successful, Err(exception) if any problems occur.
        Successfully loaded contracts are stored in self.live_contracts.
        """
        try:
            if not self.contract_file.exists():
                return Ok([])

            with open(self.contract_file, "r") as f:
                contract_data = json.load(f)

            contracts = []
            for item in contract_data:
                try:
                    contract = DispatchContract.model_validate(item)
                    if contract.is_live():
                        self.live_contracts[contract.ContractId] = contract
                        contracts.append(contract)
                except Exception as e:
                    # Log but continue processing other contracts
                    print(f"Error parsing contract: {e}")
                    continue

            return Ok(contracts)

        except Exception as e:
            return Err(Exception(f"Failed to load contracts: {str(e)}"))

    def save_contract(self, contract: DispatchContract) -> Result[bool, Exception]:
        """Save a new contract to persistent storage"""
        try:
            contracts = []
            if self.contract_file.exists():
                with open(self.contract_file, "r") as f:
                    contracts = json.load(f)

            # Add new contract
            contracts.append(contract.model_dump())

            # Remove any expired contracts while we're at it
            now = time.time()
            contracts = [c for c in contracts 
                        if now < c["StartUnixS"] + c["DurationMinutes"] * 60]

            with open(self.contract_file, "w") as f:
                json.dump(contracts, f, indent=2)

            if contract.is_live():
                self.live_contracts[contract.ContractId] = contract

            return Ok(True)

        except Exception as e:
            return Err(Exception(f"Failed to save contract: {str(e)}"))

    def add_contract(self, contract: DispatchContract) -> None:
        """Add a new contract, ensuring market type is supported"""
        market_type_name = contract.market_type_name
        if market_type_name not in self.supported_markets:
            raise ValueError(f"Unsupported market type {market_type_name}")
            
        active_market = self.supported_markets[market_type_name]
        if contract.MarketSlotName not in active_market.active_slots:
            active_market.active_slots[contract.MarketSlotName] = MarketSlotContracts(
                contract.MarketSlotName
            )
        active_market.active_slots[contract.MarketSlotName].add_contract(contract)
        
    def get_energy_instruction(self) -> Optional[EnergyInstruction]:
        """Create a single EnergyInstruction from all active validated contracts
        
        Currently only handles Rt60Gate5 market type. Future enhancement will
        need to handle multiple market types and ensure consistency.
        """
        rt60 = self.supported_markets[MarketTypeName.rt60gate5]
        
        # Find the currently active market slot
        active_slot_name = None
        for slot_name in rt60.active_slots:
            contracts = rt60.active_slots[slot_name]
            agg = contracts.get_aggregated_contract()
            if agg and agg.is_live():
                active_slot_name = slot_name
                break
                
        if not active_slot_name:
            return None
            
        agg_contract = rt60.active_slots[active_slot_name].get_aggregated_contract()
        if not agg_contract:
            return None
            
        return EnergyInstruction(
            FromGNodeAlias=agg_contract.BidderAlias,
            SlotStartS=agg_contract.StartUnixS,
            SlotDurationMinutes=agg_contract.DurationMinutes,
            SendTimeMs=int(time.time() * 1000),
            AvgPowerWatts=agg_contract.AvgPowerWatts
        )
        
    def process_message(self, message: Message) -> Result[bool, BaseException]:
        """Process incoming messages"""
        match message.Payload:
            case MarketMakerAck():
                # Update contract validation status
                self.market_maker_ack_received(message.Payload)
                
        return Ok(True)

    def all_live_contracts_acked(self) -> bool:
        ... # TODO: check if all active_slots are ValidatedByMarketMaker

    def market_maker_ack_received(self, payload: MarketMakerAck) -> None:
        market_type_name =  payload.MarketType
        if market_type_name not in self.supported_markets:
            return Ok(True)
            
        active_market = self.supported_markets[market_type_name]
        if payload.MarketSlotName in active_market.active_slots:
            slot = active_market.active_slots[payload.MarketSlotName]
            if payload.ContractId in slot.contracts:
                contract = slot.contracts[payload.ContractId]
                contract.ValidatedByMarketMaker = True
                
               
                if slot.all_contracts_acked():
                    instruction = self.get_energy_instruction()
                    if instruction:
                        self._send_to(self.atomic_ally, instruction)

                # #TODO: Add this to a main loop.
                # # If more than one minute past past gate closing, generate new energy instruction
                # market_type = active_market.market_type
                # if (time.time() - 60 > contract.StartUnixS - 
                #         market_type.gate_closing_seconds):
    