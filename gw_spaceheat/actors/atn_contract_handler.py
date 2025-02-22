import json
import random
import time
from pathlib import Path
from typing import Optional

import pytz
from data_classes.house_0_layout import House0Layout
from data_classes.house_0_names import H0N
from enums import ContractStatus, LogLevel, RepresentationStatus
from gwproactor.logger import LoggerOrAdapter
from gwproto.data_classes.sh_node import ShNode
from named_types import Glitch, SetRepresentationStatus, SlowContractHeartbeat

from actors.config import ScadaSettings
from actors.scada_data import ScadaData

class AtnContractHandler:
    """Handles ATN's representation contract and dispatch contracts w SCADA"""

    DONE_STATES = [
        ContractStatus.TerminatedByAtn,
        ContractStatus.TerminatedByScada,
        ContractStatus.CompletedUnknownOutcome,
        ContractStatus.CompletedSuccess,
        ContractStatus.CompletedFailureByAtn,
        ContractStatus.CompletedFailureByScada,
    ]
    GRACE_PERIOD_MINUTES = 5  # Time after contract end before auto-ready
    LOGGER_NAME = "AtnContractHandler"

    def __init__(
        self,
        settings: ScadaSettings,
        layout: House0Layout,
        node: ShNode,  # intended to be H0N.primary_scada
        logger: LoggerOrAdapter,
        data: ScadaData,
    ):
        self.settings = settings
        self.layout = layout
        self.node = node
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.logger = logger
        self.contract_file = Path(
            f"{self.settings.paths.data_dir}/slow_dispatch_contract.json"
        )
        self.data = data
        self.status: RepresentationStatus = (
            RepresentationStatus.Dormant
        )  # Start dormant until initialized
        self.latest_scada_hb: Optional[SlowContractHeartbeat] = None

    def load_heartbeat(self) -> Optional[SlowContractHeartbeat]:
        """Loads existing SlowDispatchContract from persistent storage

        - Returns a new SlowDispatchContract with state CompletedUnknownOutcome
        if the passing of time mandates a state change.
        - If the hb doesn't exist, doesn't load anyting and returns None
        - If the hb exists and covered by current time, sets self.hb
        to this heartbeat and returns None
        """
        if not self.contract_file.exists():  # no file
            self.logger.info("No contract")
            return
        with open(self.contract_file, "r") as f:
            contract_data = json.load(f)

        try:
            hb = SlowContractHeartbeat.model_validate(contract_data)
            if hb.FromNode != H0N.atn:
                raise Exception(
                    f"Should store last hb from atn ('a'), not {hb.FromNode}"
                )
            if hb.Status in self.DONE_STATES:
                self.prev = hb
                self.logger.info("Loaded ContractHb into prev")
                return None
            elif hb.Status in [
                ContractStatus.Created,
                ContractStatus.Confirmed,
                ContractStatus.Active,
            ]:  # one of the atn states
                if time.time() > hb.Contract.ContractEndS:
                    self.prev = SlowContractHeartbeat(
                        FromNode=self.node.name,
                        Contract=hb.Contract,
                        PreviousStatus=hb.Status,
                        Status=ContractStatus.CompletedUnknownOutcome,
                        MessageCreatedMs=int(time.time() * 1000),
                        Cause="Set by Scada on rebooting",
                        YourLastDigit=hb.MyDigit,
                        MyDigit=random.choice(range(10)),
                    )
                    self.logger.info(
                        "Contract expired! Should send hb to atn ASAP."
                        "Loaded ContractHb into prev"
                    )
                    return self.prev
                else:
                    self.latest_atn_hb = hb
                    self.logger.info("Loaded ContractHb into hb")
                    return None
            else:
                raise ValueError(f"Unexpected contract status {hb.Status}")
                # self.logger.warning(f"Unexpected contract status {hb.Status}")
        except Exception as e:
            raise ValueError(f"Issue loading contract! {e}")
            # self.logger.warning(f"Issue loading contract! {e}")

    def store_heartbeat(self) -> None:
        """Stores existing SlowDispatchContract to persistent storage

        Does not expect to store Created, Received or Confirmed.
        """
        if self.latest_scada_hb is None:
            raise ValueError("Do not expect to store_heartbeat when None")
        elif self.latest_scada_hb.Status not in self.DONE_STATES + [
            ContractStatus.Active
        ]:
            raise ValueError(
                f"Does not expect to store a {self.latest_scada_hb.Status.value} Status "
            )
        ...  # TODO: write self.hb to self.contract_file

    def clear_heartbeat(self) -> None:
        """Removes existing SlowDispatchContract from

        Does not expect to store Created, Received or Confirmed.
        """
        ...  # TODO: delete self.contract_file

    def initialize(self) -> Optional[SlowContractHeartbeat]:
        """Set initial status and contract state based on persistent store.

        Returns a heartbeat if contract has become expired
        """
        return_hb = self.load_heartbeat()  # None unless returning expired HB to atn
        if self.settings.representation_dormant:
            self.status = RepresentationStatus.Dormant
        else:
            if self.in_grace_period():  #
                self.status = RepresentationStatus.Active
            else:
                self.status = RepresentationStatus.Ready
        self.logger.info("Starting in %s state", self.status.value)
        return return_hb

    def in_grace_period(self) -> bool:
        """Scada is NOT dormant, and a contract is active or was active within 5 minutes"""
        if self.status == RepresentationStatus.Dormant:
            return False
        if self.latest_scada_hb:
            return True
        elif not self.prev:
            return False
        elif time.time() > self.prev.grace_period_end_s():
            return False
        else:
            return True


    def process_set_status(self, cmd: SetRepresentationStatus) -> Optional[Glitch]:
        """Handle SetRepresentationStatus command from ATN"""
        prior_status = self.status

        if cmd.Status == RepresentationStatus.Dormant:
            if self.latest_scada_hb:
                return Glitch(
                    FromGNodeAlias=self.layout.scada_g_node_alias,
                    Node=self.node.name,
                    Type=LogLevel.Warning,
                    Summary="Cannot transition to Dormant - active contract exists",
                    Details=f"Latest Contract hb: {self.latest_scada_hb.model_dump_json()}",
                )
            self.status = RepresentationStatus.Dormant
        elif cmd.Status == RepresentationStatus.Active:
            self.status = RepresentationStatus.Active

        if self.status != prior_status:
            msg = f"Status changed: {prior_status} -> {self.status}"
            if cmd.Reason:
                msg += f" Reason: {cmd.Reason}"
            self.logger.info(msg)
        return None

    def process_contract_hb(
        self, atn_hb: SlowContractHeartbeat
    ) -> Optional[SlowContractHeartbeat]:
        """Handles contract heartbeating with atn.
        If the atn_hb is appropriate:
            - Returns the heartbeat to send back to the atn
            - saves inbound atn_hb to self.latest_atn_hb and non-volatile stoarge
        Inappropriate hb if:
            - Representation status is Dormant
            - inbound hb

        """

        return_hb = None

        if self.status == RepresentationStatus.Dormant:
            self.logger.info("Ignoring atn contract hb - Dormant!")
            if self.latest_scada_hb:
                if atn_hb.Contract == self.latest_scada_hb.Contract:
                    return_hb = SlowContractHeartbeat(
                        FromNode=self.node.Name,
                        Contract=atn_hb.Contract,
                        PreviousStatus=atn_hb.Status,
                        Status=ContractStatus.TerminatedByScada,
                        Cause="Scada's records show Dormant RepresentatationStatus",
                        MessageCreatedMs=int(time.time() * 1000),
                        MyDigit=random.choice(range(10)),
                        YourLastDigit=atn_hb.MyDigit,
                    )
            self.prev = None
            self.atn_hb = None

        else:  # representation status either Ready or Active
            if atn_hb.Status == ContractStatus.Created:
                if self.latest_scada_hb:
                    self.logger.info(
                        "Received Created when I already have an existing atn_hb. Ignoring!"
                    )
                    return_hb = None
                else:
                    return_hb = self.start_new_contract_hb(atn_hb)
            else:  # Otherwise we should share the same hb
                if self.latest_scada_hb is None:
                    self.logger.warning(
                        f"my hb is None but received this hb. Ignoring! \n{atn_hb}"
                    )
                    return_hb = None
                elif self.latest_scada_hb.Contract != atn_hb.Contract:
                    self.logger.warning(
                        f"my contract is not the same as incoming! Ignoring! Mine: {self.latest_scada_hb.Contract}\n incoming: {atn_hb.Contract}"
                    )
                    return_hb = None
                else:
                    return_hb = self.update_existing_contract_hb(atn_hb)

        if return_hb is None:
            self.logger.warning("Returning no hb")
        else:
            # TODO: include start, stop time in local timezone human readable and AvgPower
            self.logger.info(f"Sending back {return_hb.Status}")
        return return_hb

    def start_new_contract_hb(
        self, atn_hb: SlowContractHeartbeat
    ) -> SlowContractHeartbeat:
        """Manage scenario where self.RepresentationStatus is Ready and we receive
        the first HB for a newly created Contract
          -  cases:
            - Prev contract exists, terminated and/or completed, inside the grace period
            - Existing contract is not completed or terminated, still
            in the existing timeframe: Ignore this one
            - Previous contract exists, outside of grace period (Ready)
            - No previous contract (Ready)
            - right now does not handle a contract for a future time slot
        """
        if self.status not in [RepresentationStatus.Ready, RepresentationStatus.Active]:
            raise Exception(
                "Can only start new contract from ready or active representation status"
            )
        if atn_hb.Status != ContractStatus.Created:
            raise Exception(
                "Can only start new contract with a ContractStatus of Created!"
            )
        if self.latest_scada_hb:
            self.logger.warning("Ignoring atn hb! Still inside existing contract")
            self.logger.warning(f"Existing: {self.latest_scada_hb}")
            raise Exception(f"Inbound: {atn_hb}")

        self.status = RepresentationStatus.Active  # representation: Ready -> Active
        self.latest_scada_hb = atn_hb
        self.store_heartbeat()
        return SlowContractHeartbeat(
            FromNode=self.node.Name,
            Contract=atn_hb.Contract,
            PreviousStatus=atn_hb.Status,
            Status=ContractStatus.Received,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=atn_hb.MyDigit,
        )

    def update_existing_contract_hb(
        self, atn_hb: SlowContractHeartbeat
    ) -> SlowContractHeartbeat:
        if self.status not in [RepresentationStatus.Ready, RepresentationStatus.Active]:
            raise Exception(
                "Do not call update_existing_contract if rep status is not Ready or Active"
            )
        if self.latest_scada_hb is None:
            raise Exception(
                "Do not call update_existing_contract_hb if latest_atn_hb is None"
            )
        if self.latest_scada_hb.Contract != atn_hb.Contract:
            raise Exception(
                "Do not call update_existing_contract if self.hb.Contract != atn_hb.Contract"
            )

        if atn_hb.Status == ContractStatus.TerminatedByAtn:  # clear out contract
            new_contract_status = atn_hb.Status
            self.prev = atn_hb
            self.latest_scada_hb = None
            self.clear_heartbeat()
        else:
            if atn_hb.Status == ContractStatus.Confirmed:
                if self.latest_scada_hb.Status != ContractStatus.Created:
                    raise Exception(
                        f"self.hb.Status is {self.latest_scada_hb.Status} instead of Created with inbound atn_hb.Status of Confirmed!"
                    )
                new_contract_status = ContractStatus.Active  # for hb back to atn
            elif atn_hb.Status == ContractStatus.Active:
                if self.latest_scada_hb.Status != ContractStatus.Confirmed:
                    raise Exception(
                        f"self.hb.Status is {self.latest_scada_hb.Status} instead of Created with inbound atn_hb.Status of Confirmed!"
                    )
                new_contract_status = ContractStatus.Active
            self.latest_scada_hb = atn_hb
            self.store_heartbeat()

        if new_contract_status != atn_hb.Status:
            prev_status = atn_hb.Status
        else:
            prev_status = None
        return SlowContractHeartbeat(
            FromNode=self.node.Name,
            Contract=atn_hb.Contract,
            PreviousStatus=prev_status,
            Status=new_contract_status,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=atn_hb.MyDigit,
        )

    def scada_terminates_contract_hb(self, cause: str = "") -> SlowContractHeartbeat:
        """Creats a heartbeat declaring scada termination of contract
        - can only call if self.latest_atn_hb exists
        - sets prev to latest_atn_hb and latest_atn_hb to None
        """
        if not self.latest_scada_hb:
            raise Exception("Cannot call scada terminates contract if no latest_atn_hb")
        hb = SlowContractHeartbeat(
            FromNode=self.node.Name,
            Contract=self.latest_scada_hb.Contract,
            PreviousStatus=self.latest_scada_hb.Status,
            Status=ContractStatus.TerminatedByScada,
            Cause=cause,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_scada_hb.MyDigit,
        )
        self.prev = hb
        self.latest_scada_hb = None
        return hb

    def scada_detects_contract_complete_hb(self) -> SlowContractHeartbeat:
        """Creats a heartbeat noting time has passed completion
        - can only call if self.latest_atn_hb exists
        - sets prev to latest_atn_hb and latest_atn_hb to None

        Raises exception if called before the ContractEndS
        """
        now = time.time()
        if not self.latest_scada_hb:
            raise Exception("Cannot call scada terminates contract if no latest_atn_hb")
        if now < self.latest_scada_hb.Contract.ContractEndS:
            raise Exception(
                f"scada_detects_contract_complete_hb called at {int(now)}, before ContractEndTime of {self.latest_scada_hb.Contract.ContractEndS}"
            )
        hb = SlowContractHeartbeat(
            FromNode=self.node.Name,
            Contract=self.latest_scada_hb.Contract,
            PreviousStatus=self.latest_scada_hb.Status,
            Status=ContractStatus.CompletedUnknownOutcome,
            MessageCreatedMs=int(time.time() * 1000),
            MyDigit=random.choice(range(10)),
            YourLastDigit=self.latest_scada_hb.MyDigit,
        )
        self.prev = hb
        self.latest_scada_hb = None
        return hb
