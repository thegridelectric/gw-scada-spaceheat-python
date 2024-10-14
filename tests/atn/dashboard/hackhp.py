import json
import logging
import time
from datetime import datetime
from enum import auto
from enum import StrEnum
from typing import Deque
from typing import Optional

import requests

from tests.atn.atn_config import HackHpSettings
from tests.atn.dashboard.channels.containers import enqueue_fifo_q
from tests.atn.dashboard.channels.containers import Channels
from tests.atn.dashboard.channels.channel import PUMP_OFF_THRESHOLD

PUMP_ON_THRESHOLD = 4
HP_DEFINITELY_HEATING_THRESHOLD = 6000
HP_DEFINITELY_OFF_THRESHOLD = 500
HP_TRYING_TO_START_THRESHOLD = 1200

class AlertPriority(StrEnum):
    P1Critical = auto()
    P2High = auto()
    P3Medium = auto()
    P4Low = auto()
    P5Info = auto()


class AlertTeam(StrEnum):
    GridWorksDev = auto()
    MosconeHeating = auto()


class OpsGeniePriority(StrEnum):
    """
    P1: Critical incidents that require immediate attention. Examples include system outages, service disruptions, or major security breaches.
    P2: High-priority incidents that require urgent attention. Examples include significant performance degradation or service degradation affecting multiple users.
    P3:  Medium-priority incidents that require attention but are not critical. Examples include minor performance issues or service disruptions affecting a small number of users.
    P4: Low-priority incidents that require attention but do not require immediate action. Examples include minor bugs, errors, or warnings.
    P5: Informational incidents that do not require immediate action. Examples include informational messages, system logs, or maintenance notifications.
    """
    P1 = auto()
    P2 = auto()
    P3 = auto()
    P4 = auto()
    P5 = auto()


def gw_to_ops_priority(gw: AlertPriority) -> OpsGeniePriority:
    """ Translates from the in-house gridworks alert priorities to OpsGenie Priorities (P1 through P5)"""
    if gw == AlertPriority.P1Critical:
        return OpsGeniePriority.P1
    elif gw == AlertPriority.P2High:
        return OpsGeniePriority.P2
    elif gw == AlertPriority.P3Medium:
        return OpsGeniePriority.P3
    elif gw == AlertPriority.P4Low:
        return OpsGeniePriority.P4
    return OpsGeniePriority.P5


def send_opsgenie_scada_alert(
    name: str,
    settings: HackHpSettings,
    node_name_short: str,
    *,
    description: Optional[str] = None,
    priority: AlertPriority = AlertPriority.P3Medium,
    alert_team: AlertTeam = AlertTeam.GridWorksDev
) -> None:
    """
    Creates an ops genie alert. The name is prepended by the short name of the SCADA
    and used to create the ops genie message.

    The OpsGenie alias is used to de-dupe alerts. OpsGenie does not issue a new alert
    if there is already an open alert with the same alias.

    The alias is the name appended with the date. For example:
      oak.store-pump-dispatch-failure.20240425
    """
    url = 'https://api.opsgenie.com/v2/alerts'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'GenieKey {settings.ops_genie_api_key}'
    }

    message = f"{node_name_short}.{name}"
    alias = f"{message}.{datetime.now().strftime('%Y-%m-%d')}"

    responders = [{
        "type": "team",
        "id": settings.gridworks_team_id
    }]
    if alert_team == AlertTeam.MosconeHeating:
        responders = [{
            "type": "team",
            "id": settings.moscone_team_id
        }]

    payload = {
        "message": message,
        "alias": alias,
        "priority": gw_to_ops_priority(priority).value,
        "responders": responders
    }
    if description:
        payload["description"] = description
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 202:
        print(f"{message} alert sent")
    else:
        print(f"Failed to send {message} alert.")
        print("Response:", response.text)


class HackHpState(StrEnum):
    Heating = auto()
    Idling = auto()
    Trying = auto()
    NoOp = auto()


class HackHpStateCapture:
    state: HackHpState
    hp_pwr_w: int
    primary_pump_pwr_w: int
    state_start_s: int
    start_attempts: int
    state_end_s: Optional[int]
    idu_pwr_w: Optional[int]
    odu_pwr_w: Optional[int]

    def __init__(self,
                 state: HackHpState = HackHpState.NoOp,
                 hp_pwr_w: int = 0,
                 primary_pump_pwr_w: int = 0,
                 state_start_s: int = int(time.time()),
                 start_attempts: int = 0,
                 state_end_s: Optional[int] = None,
                 idu_pwr_w: Optional[int] = None,
                 odu_pwr_w: Optional[int] = None,

                 ):
        self.state = state
        self.hp_pwr_w = hp_pwr_w
        self.primary_pump_pwr_w = primary_pump_pwr_w
        self.state_start_s = state_start_s
        self.start_attempts = start_attempts
        self.state_end_s = state_end_s
        self.idu_pwr_w = idu_pwr_w
        self.odu_pwr_w = odu_pwr_w

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return (
            f"State: {self.state}, Hp: {self.hp_pwr_w} W, IDU: {self.idu_pwr_w} "
            f"W, ODU: {self.odu_pwr_w} W, Pump: {self.primary_pump_pwr_w}, "
            f"Time: {datetime.fromtimestamp(self.state_start_s)}"
        )

class HackHp:

    state_q: Deque[HackHpStateCapture]
    settings: HackHpSettings
    short_name: str
    raise_dashboard_exceptions: bool
    logger: logging.Logger | logging.LoggerAdapter

    def __init__(
        self,
        settings: HackHpSettings,
        short_name: str,
        raise_dashboard_exceptions: bool = False,
        logger: Optional[logging.Logger | logging.LoggerAdapter] = None,
    ):
        self.settings = settings
        self.short_name = short_name
        self.raise_dashboard_exceptions = raise_dashboard_exceptions
        self.logger = logger
        self.state_q = Deque[HackHpStateCapture](maxlen=10)
        self.state_q.append(HackHpStateCapture())

    def update_pwr(
        self,
        *,
        fastpath_pwr_w: Optional[float],
        channels: Channels,
        report_time_s: int,
    ) -> None:
        try:
            now = int(time.time())
            if fastpath_pwr_w is not None:
                # fastpath does not include the breakdown between
                # idu and odu power
                hp_pwr_w = fastpath_pwr_w
                idu_pwr_w = None
                odu_pwr_w = None
            else:
                if (
                    not channels.power.hp_indoor or
                    not channels.power.hp_outdoor or
                    not channels.power.hp_indoor.reading or
                    not not channels.power.hp_outdoor.reading
                ):
                    return
                if now - report_time_s > 5:
                    return
                idu_pwr_w = channels.power.hp_indoor.reading.raw
                odu_pwr_w = channels.power.hp_outdoor.reading.raw
                hp_pwr_w = idu_pwr_w + odu_pwr_w

            primary_pump_pwr_w = channels.power.pumps.primary.reading.raw

            if (self.state_q[0].state != HackHpState.Heating and
                    hp_pwr_w > HP_DEFINITELY_HEATING_THRESHOLD):
                # add a new "DefinitelyHeating" capture to the front of the queue
                hp_state_capture = HackHpStateCapture(
                    state=HackHpState.Heating,
                    hp_pwr_w=hp_pwr_w,
                    primary_pump_pwr_w=primary_pump_pwr_w,
                    state_start_s=report_time_s,
                    idu_pwr_w=idu_pwr_w,
                    odu_pwr_w=odu_pwr_w,
                )
                if self.state_q[0].start_attempts > 1:
                    send_opsgenie_scada_alert(
                        name="hp-finally-heating",
                        settings=self.settings,
                        node_name_short=self.short_name,
                        description=f"Heat pump started heating after {self.state_q[0].start_attempts} attempts to start",
                        alert_team=AlertTeam.MosconeHeating,
                        priority=AlertPriority.P5Info
                    )
                self.state_q[0].state_end_s = now
                enqueue_fifo_q(hp_state_capture, self.state_q)
            elif (self.state_q[0].state != HackHpState.NoOp and
                  hp_pwr_w < HP_DEFINITELY_OFF_THRESHOLD and
                  primary_pump_pwr_w < PUMP_OFF_THRESHOLD):
                # add a new "NotDefinitelyHeating" capture to the front of the queue
                hp_state_capture = HackHpStateCapture(
                    state=HackHpState.NoOp,
                    hp_pwr_w=hp_pwr_w,
                    primary_pump_pwr_w=primary_pump_pwr_w,
                    state_start_s=report_time_s,
                    idu_pwr_w=idu_pwr_w,
                    odu_pwr_w=odu_pwr_w,
                )
                self.state_q[0].state_end_s = now
                enqueue_fifo_q(hp_state_capture, self.state_q)
            elif (self.state_q[0].state == HackHpState.Heating and
                  hp_pwr_w < HP_DEFINITELY_OFF_THRESHOLD and
                  primary_pump_pwr_w > PUMP_ON_THRESHOLD):
                # add a new "NotDefinitelyHeating" capture to the front of the queue
                hp_state_capture = HackHpStateCapture(
                    state=HackHpState.Idling,
                    hp_pwr_w=hp_pwr_w,
                    primary_pump_pwr_w=primary_pump_pwr_w,
                    state_start_s=report_time_s,
                    idu_pwr_w=idu_pwr_w,
                    odu_pwr_w=odu_pwr_w,
                )
                self.state_q[0].state_end_s = now
                enqueue_fifo_q(hp_state_capture, self.state_q)
            elif (self.state_q[0].state == HackHpState.NoOp
                  and primary_pump_pwr_w > PUMP_ON_THRESHOLD):
                hp_state_capture = HackHpStateCapture(
                    state=HackHpState.Idling,
                    hp_pwr_w=hp_pwr_w,
                    primary_pump_pwr_w=primary_pump_pwr_w,
                    state_start_s=report_time_s,
                    idu_pwr_w=idu_pwr_w,
                    odu_pwr_w=odu_pwr_w,
                )
                self.state_q[0].state_end_s = now
                enqueue_fifo_q(hp_state_capture, self.state_q)
            elif (self.state_q[0].state == HackHpState.Idling
                  and hp_pwr_w > HP_TRYING_TO_START_THRESHOLD):
                # update the HackHpStateCapture state from ProbablyResting to TryingToStart
                # and increment the start attempts
                self.state_q[0].state = HackHpState.Trying
                self.state_q[0].start_attempts += 1
                self.state_q[0].hp_pwr_w = hp_pwr_w
                self.state_q[0].idu_pwr_w = idu_pwr_w
                self.state_q[0].odu_pwr_w = odu_pwr_w
                self.state_q[0].primary_pump_pwr_w = primary_pump_pwr_w
            elif (self.state_q[0].state == HackHpState.Trying
                  and hp_pwr_w < HP_DEFINITELY_OFF_THRESHOLD):
                self.state_q[0].state = HackHpState.Idling
                self.state_q[0].hp_pwr_w = hp_pwr_w
                self.state_q[0].idu_pwr_w = idu_pwr_w
                self.state_q[0].odu_pwr_w = odu_pwr_w
                self.state_q[0].primary_pump_pwr_w = primary_pump_pwr_w
            else:
                # just update the current state
                self.state_q[0].hp_pwr_w = hp_pwr_w
                self.state_q[0].idu_pwr_w = idu_pwr_w
                self.state_q[0].odu_pwr_w = odu_pwr_w
                self.state_q[0].primary_pump_pwr_w = primary_pump_pwr_w

            if self.state_q[0].start_attempts > 1:
                send_opsgenie_scada_alert(
                    name="hp-retrying",
                    settings=self.settings,
                    node_name_short=self.short_name,
                    description=f"Heat pump has taken {self.state_q[0].start_attempts} to start",
                    alert_team=AlertTeam.MosconeHeating
                )
        except Exception as e:
            self.logger.error("ERROR in refresh_gui")
            self.logger.exception(e)
            if self.raise_dashboard_exceptions:
                raise
