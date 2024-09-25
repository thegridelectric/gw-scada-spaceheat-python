"""Scratch atn implementation"""
from collections import defaultdict

PUMP_OFF_THRESHOLD = 2
PUMP_ON_THRESHOLD = 4
HP_DEFINITELY_HEATING_THRESHOLD = 6000
HP_DEFINITELY_OFF_THRESHOLD = 500
HP_TRYING_TO_START_THRESHOLD = 1200
import json
import asyncio
import dataclasses
import threading
import time
import requests
from dataclasses import dataclass
from typing import Any
from typing import cast
from typing import Deque
from typing import Optional
from typing import Sequence
from typing import Tuple

from fastapi_utils.enums import StrEnum
from enum import auto

import pendulum
from paho.mqtt.client import MQTTMessageInfo
import rich
from rich.table import Table
from rich.text import Text, Style

from pydantic import BaseModel

from gwproto import CallableDecoder
from gwproto import Decoders
from gwproto import create_message_payload_discriminator
from gwproto import MQTTCodec
from gwproto import MQTTTopic
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName
from gwproto.messages import GtShStatusEvent
from gwproto.messages import SnapshotSpaceheatEvent
from gwproto.messages import EventBase
from gwproto.messages import PowerWatts
from gwproto.messages import PowerWatts_Maker
from gwproto.messages import GtDispatchBoolean_Maker
from gwproto.messages import GtShCliAtnCmd_Maker
from gwproto.messages import GtShStatus
from gwproto.messages import SnapshotSpaceheat
from gwproto.messages import GsPwr_Maker
from gwproto.messages import GtShStatus_Maker
from gwproto.messages import SnapshotSpaceheat_Maker
from gwproto.types import TelemetrySnapshotSpaceheat

from gwproactor import ActorInterface
from gwproactor import QOS
from gwproactor.message import DBGCommands
from gwproactor.message import DBGPayload
from gwproactor.config import LoggerLevels
from gwproactor.message import MQTTReceiptPayload, Message
from gwproactor.proactor_implementation import Proactor

from gwproto.enums import Role
from actors import message as actor_message # noqa


from tests.atn import messages
from tests.atn.atn_config import AtnSettings

AtnMessageDecoder = create_message_payload_discriminator(
    model_name="AtnMessageDecoder",
    module_names=["gwproto.messages", "gwproactor.message", "actors.message", ],
    modules=[messages],
)


GRIDWORKS_DEV_OPS_GENIE_TEAM_ID = "edaccf48-a7c9-40b7-858a-7822c6f862a4"
MOSCONE_HEATING_OPS_GENIE_TEAM_ID = "d1ddacdd-7ab4-4fa2-83ea-06eddcf5b273"


from fastapi_utils.enums import StrEnum
from enum import auto
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


def send_opsgenie_scada_alert(name: str,
                              settings: AtnSettings, 
                              layout: HardwareLayout,
                              description: Optional[str] = None,
                              priority: AlertPriority = AlertPriority.P3Medium,
                              alert_team: AlertTeam = AlertTeam.GridWorksDev):
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
    
    node_short_name = layout.atn_g_node_alias.split('.')[-1]
    message = f"{node_short_name}.{name}"
    ft = pendulum.now("America/New_York").format("YYYY-MM-DD")
    alias = f"{message}.{ft}"
    
    responders = [{
                "type": "team",
                "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID
            }]
    if alert_team == AlertTeam.MosconeHeating:
        responders = [{
                "type": "team",
                "id": MOSCONE_HEATING_OPS_GENIE_TEAM_ID
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

class PumpPowerState(StrEnum):
    NoFlow = auto()
    Flow = auto()

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
            state: HackHpState=HackHpState.NoOp,
            hp_pwr_w: int=0, 
            primary_pump_pwr_w: int=0,
            state_start_s: int = int(time.time()),
            start_attempts: int = 0,
            state_end_s: Optional[int] = None,
            idu_pwr_w: Optional[int]=None, 
            odu_pwr_w: Optional[int]=None, 
            
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
        return (f"State: {self.state}, Hp: {self.hp_pwr_w} W, IDU: {self.idu_pwr_w} W, ODU: {self.odu_pwr_w} W, Pump: {self.primary_pump_pwr_w}, Time: {pendulum.from_timestamp(self.state_start_s).in_tz('America/New_York')}")

    def __repr__(self):
        return (f"State: {self.state}, Hp: {self.hp_pwr_w} W, IDU: {self.idu_pwr_w} W, ODU: {self.odu_pwr_w} W, Pump: {self.primary_pump_pwr_w}, Time: {pendulum.from_timestamp(self.state_start_s).in_tz('America/New_York')}")

class Tank:
    idx: int
    t1: ShNode
    t2: ShNode
    t3: ShNode
    t4: ShNode
    is_buffer: bool

    def __init__(
            self, idx, t1, t2, t3, t4, is_buffer: bool = False
    ):
        self.idx = idx
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.t4 = t4
        is_buffer = is_buffer


class Stat:
    idx: int
    display_name: str
    set: ShNode
    wall_unit_temp: ShNode
    gw_temp: Optional[ShNode] = None

    def __init__(
            self, idx, display_name, set, wall_unit_temp, gw_temp
    ):
        self.idx = idx
        self.display_name = display_name
        self.set = set
        self.wall_unit_temp = wall_unit_temp
        self.gw_temp = gw_temp

class AtnMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            Decoders.from_objects(
                [
                    GtShStatus_Maker,
                    SnapshotSpaceheat_Maker,
                    PowerWatts_Maker,
                ],
                message_payload_discriminator=AtnMessageDecoder,
            ).add_decoder("p", CallableDecoder(lambda decoded: GsPwr_Maker(decoded[0]).tuple))
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.scada_g_node_alias:
            raise Exception(f"alias {source_alias} not my Scada!")

class Telemetry(BaseModel):
    Value: int
    Unit: TelemetryName

class RecentRelayState(BaseModel):
    State: Optional[int] = None
    LastChangeTimeUnixMs: Optional[int] = None




@dataclass
class AtnData:
    prev_prev_snapshot: Optional[SnapshotSpaceheat] = None
    prev_snapshot: Optional[SnapshotSpaceheat] = None
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_status: Optional[GtShStatus] = None
    relay_state: dict[ShNode, RecentRelayState] = dataclasses.field(default_factory=dict)

class Atn(ActorInterface, Proactor):
    SCADA_MQTT = "scada"
    is_oak: bool
    data: AtnData
    my_sensors: Sequence[ShNode]
    my_relays: Sequence[ShNode]
    event_loop_thread: Optional[threading.Thread] = None

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self._web_manager.disable()
        self.my_sensors = list(
            filter(
                lambda x: (
                    x.role == Role.TankWaterTempSensor
                    or x.role == Role.BooleanActuator
                    or x.role == Role.PipeTempSensor
                    or x.role == Role.PipeFlowMeter
                    or x.role == Role.PowerMeter
                ),
                list(self.layout.nodes.values()),
            )
        )
        atn_alias = self.layout.atn_g_node_alias
        short_name = atn_alias.split(".")[-1]
        if short_name == "oak":
            self.is_oak = True
        else:
            self.is_oak = False
        
        self.my_relays = list(
            filter(lambda x: x.role == Role.BooleanActuator, list(self.layout.nodes.values()))
        )
        self.data = AtnData(relay_state={x: RecentRelayState() for x in self.my_relays})
        self._links.add_mqtt_link(Atn.SCADA_MQTT, self.settings.scada_mqtt, AtnMQTTCodec(self.layout), primary_peer=True)
        self._links.subscribe(
            Atn.SCADA_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), self.layout.scada_g_node_alias),
            QOS.AtMostOnce,
        )

        self.latest_status: Optional[GtShStatus] = None
        self.status_output_dir = self.settings.paths.data_dir / "status"
        self.status_output_dir.mkdir(parents=True, exist_ok=True)

        self.store_discharge_flow_node = self.layout.nodes["store.discharge.flow"]
        self.dist_flow_node = self.layout.nodes["dist.flow"]
        self.primary_flow_node = self.layout.nodes["primary.flow"]
        self.flow_nodes = [
            self.primary_flow_node,
            self.dist_flow_node,
            self.store_discharge_flow_node,
        ]
        self.fastpath_pwr_w: int = 0
        self.hp_indoor_power_node = self.layout.nodes["hp.indoor.power"]
        self.hp_outdoor_power_node = self.layout.nodes["hp.outdoor.power"]
        self.primary_pump_power_node = self.layout.nodes["primary.pump.power"]
        self.store_pump_power_node = self.layout.nodes["store.pump.power"]
        self.dist_pump_power_node = self.layout.nodes["dist.pump.power"]
        self.oil_pump_power_node = self.layout.nodes["oil.boiler.power"]

        self.hp_lwt_temp_node = self.layout.nodes["a.hp.lwt.temp"]
        self.hp_ewt_temp_node = self.layout.nodes["a.hp.ewt.temp"]

        self.dist_swt_temp_node = self.layout.nodes["a.dist.fwt.temp"]
        self.dist_rwt_temp_node = self.layout.nodes["a.dist.rwt.temp"]

        self.store_hot_pipe_temp_node = self.layout.nodes["a.store.hot.pipe.temp"]
        self.store_cold_pipe_temp_node = self.layout.nodes["a.store.cold.pipe.temp"]

        self.buffer_hot_pipe_temp_node = self.layout.nodes["a.buffer.hot.pipe.temp"]
        self.buffer_cold_pipe_temp_node = self.layout.nodes["a.buffer.cold.pipe.temp"]

        self.initialize_stats()

        # from collections import deque
        self.dist_pump_pwr_state_q: Deque[Tuple[PumpPowerState, int, int]] = Deque(maxlen=10)
        self.dist_pump_pwr_state: PumpPowerState = PumpPowerState.NoFlow
        self.hack_hp_state_q: Deque[HackHpStateCapture] = Deque(maxlen=10) # enum, idu_pwr_w, odu_pwr_w, time
        self.hack_hp_state_q.append(HackHpStateCapture())
        self.buffer: Tank = Tank(idx = 1,
                      t1 = self.layout.nodes["buffer.temp.depth1"],
                      t2 = self.layout.nodes["buffer.temp.depth2"],
                      t3 = self.layout.nodes["buffer.temp.depth3"],
                      t4 = self.layout.nodes["buffer.temp.depth4"],
                      is_buffer = True
                      )
            
        if self.is_oak:
            self.store = {1: Tank(idx=1,
                      t1 = self.layout.nodes["tank1.temp.depth1"],
                      t2 = self.layout.nodes["tank1.temp.depth2"],
                      t3 = self.layout.nodes["tank1.temp.depth3"],
                      t4 = self.layout.nodes["tank1.temp.depth4"],
                      is_buffer = False
                      ),
                    2: Tank(idx=1,
                      t1 = self.layout.nodes["tank1.temp.depth1"], # oak tank 2 hack
                      t2 = self.layout.nodes["tank1.temp.depth2"],
                      t3 = self.layout.nodes["tank1.temp.depth3"],
                      t4 = self.layout.nodes["tank1.temp.depth4"],
                      is_buffer = False
                      ),
                    3: Tank(idx=1,
                      t1 = self.layout.nodes["tank3.temp.depth1"],
                      t2 = self.layout.nodes["tank3.temp.depth2"],
                      t3 = self.layout.nodes["tank3.temp.depth3"],
                      t4 = self.layout.nodes["tank3.temp.depth4"],
                      is_buffer = False
                      )
        }
        else:
            self.store = {1: Tank(idx=1,
                        t1 = self.layout.nodes["tank1.temp.depth1"],
                        t2 = self.layout.nodes["tank1.temp.depth2"], # beech temp 2 hack
                        t3 = self.layout.nodes["tank1.temp.depth3"],
                        t4 = self.layout.nodes["tank1.temp.depth4"],
                        is_buffer = False
                        ),
                        2: Tank(idx=1,
                        t1 = self.layout.nodes["tank2.temp.depth1"],
                        t2 = self.layout.nodes["tank2.temp.depth2"],
                        t3 = self.layout.nodes["tank2.temp.depth3"],
                        t4 = self.layout.nodes["tank2.temp.depth4"],
                        is_buffer = False
                        ),
                        3: Tank(idx=1,
                        t1 = self.layout.nodes["tank3.temp.depth1"],
                        t2 = self.layout.nodes["tank3.temp.depth2"],
                        t3 = self.layout.nodes["tank3.temp.depth3"],
                        t4 = self.layout.nodes["tank3.temp.depth4"],
                        is_buffer = False
                        )
            }

    def initialize_stats(self):
        self.stat = {}   
        if self.is_oak:
            self.stat = {
                1: Stat(idx=1, 
                        display_name="Living Rm",
                        set=self.layout.nodes["livingrm.set"],
                        wall_unit_temp=self.layout.nodes["livingrm.temp"],
                        gw_temp=None),
                2: Stat(idx=2, 
                        display_name="Garage",
                        set=self.layout.nodes["garage.set"],
                        wall_unit_temp=self.layout.nodes["garage.temp"],
                        gw_temp=None),
                3: Stat(idx=3, 
                        display_name="Gear Room",
                        set=self.layout.nodes["gear.set"],
                        wall_unit_temp=self.layout.nodes["gear.temp"],
                        gw_temp=None),
                4: Stat(idx=4, 
                        display_name="Upstairs",
                        set=self.layout.nodes["upstairs.set"],
                        wall_unit_temp=self.layout.nodes["upstairs.temp"],
                        gw_temp=None),
            } 
        else:
            self.stat = {
                1: Stat(idx=1, 
                        display_name="Living Rm",
                        set=self.layout.nodes["a.thermostat.downstairs.set"],
                        wall_unit_temp=self.layout.nodes["a.thermostat.downstairs.temp"],
                        gw_temp = self.layout.nodes["stat1.temp"]),
                2: Stat(idx=2, 
                        display_name="Up",
                        set=self.layout.nodes["a.thermostat.upstairs.set"],
                        wall_unit_temp=self.layout.nodes["a.thermostat.upstairs.temp"],
                        gw_temp = self.layout.nodes["stat2.temp"])
            }


    @property
    def alias(self) -> str:
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def publication_name(self) -> str:
        return self.layout.atn_g_node_alias

    @property
    def settings(self) -> AtnSettings:
        return cast(AtnSettings, self._settings)

    @property
    def layout(self) -> HardwareLayout:
        return self._layout

    def init(self):
        """Called after constructor so derived functions can be used in setup."""


    def _publish_to_scada(self, payload, qos: QOS = QOS.AtMostOnce) -> MQTTMessageInfo:
        return self._links.publish_message(
            Atn.SCADA_MQTT,
            Message(Src=self.publication_name, Payload=payload),
            qos=qos
        )
    
    def hack_update_hp_pwr(self, from_fastpath: bool = False) -> None:
        now = int(time.time())
        if self.data.latest_snapshot is None:
            return
        snap = self.data.latest_snapshot.Snapshot
        if from_fastpath:
            # fastpath does not include the breakdown between
            # idu and odu power
            hp_pwr_w = self.fastpath_pwr_w
            report_time_s = now
            idu_pwr_w = None
            odu_pwr_w = None
        else:
            report_time_s = int(snap.ReportTimeUnixMs / 1000)
            if now - report_time_s > 5:
                # Data is stale. Don't update 
                return
            idu_idx = snap.AboutNodeAliasList.index(self.hp_indoor_power_node.alias)
            odu_idx = snap.AboutNodeAliasList.index(self.hp_outdoor_power_node.alias)
            idu_pwr_w = snap.ValueList[idu_idx] 
            odu_pwr_w = snap.ValueList[odu_idx] 
            hp_pwr_w = idu_pwr_w + odu_pwr_w

        primary_idx = snap.AboutNodeAliasList.index(self.primary_pump_power_node.alias)
        primary_pump_pwr_w = snap.ValueList[primary_idx]

        if (self.hack_hp_state_q[0].state != HackHpState.Heating and 
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
            if self.hack_hp_state_q[0].start_attempts > 1:
                send_opsgenie_scada_alert(
                    name="hp-finally-heating",
                    settings=self.settings,
                    layout=self.layout,
                    description=f"Heat pump started heating after {self.hack_hp_state_q[0].start_attempts} attempts to start",
                    alert_team=AlertTeam.MosconeHeating,
                    priority=AlertPriority.P5Info
                )
            self.hack_hp_state_q[0].state_end_s = now
            self.enqueue_fifo_q(hp_state_capture, self.hack_hp_state_q)
        elif (self.hack_hp_state_q[0].state != HackHpState.NoOp and 
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
            self.hack_hp_state_q[0].state_end_s = now
            self.enqueue_fifo_q(hp_state_capture, self.hack_hp_state_q)
        elif (self.hack_hp_state_q[0].state == HackHpState.Heating and 
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
            self.hack_hp_state_q[0].state_end_s = now
            self.enqueue_fifo_q(hp_state_capture, self.hack_hp_state_q)
        elif (self.hack_hp_state_q[0].state == HackHpState.NoOp
              and primary_pump_pwr_w > PUMP_ON_THRESHOLD):
            hp_state_capture = HackHpStateCapture(
                    state=HackHpState.Idling,
                    hp_pwr_w=hp_pwr_w,
                    primary_pump_pwr_w=primary_pump_pwr_w,
                    state_start_s=report_time_s,
                    idu_pwr_w=idu_pwr_w,
                    odu_pwr_w=odu_pwr_w,
                )
            self.hack_hp_state_q[0].state_end_s = now
            self.enqueue_fifo_q(hp_state_capture, self.hack_hp_state_q)
        elif (self.hack_hp_state_q[0].state == HackHpState.Idling
              and hp_pwr_w > HP_TRYING_TO_START_THRESHOLD):
            # update the HackHpStateCapture state from ProbablyResting to TryingToStart
            # and increment the start attempts
            self.hack_hp_state_q[0].state = HackHpState.Trying
            self.hack_hp_state_q[0].start_attempts += 1
            self.hack_hp_state_q[0].hp_pwr_w = hp_pwr_w
            self.hack_hp_state_q[0].idu_pwr_w = idu_pwr_w
            self.hack_hp_state_q[0].odu_pwr_w = odu_pwr_w
            self.hack_hp_state_q[0].primary_pump_pwr_w = primary_pump_pwr_w
        elif (self.hack_hp_state_q[0].state == HackHpState.Trying
              and hp_pwr_w < HP_DEFINITELY_OFF_THRESHOLD):
            self.hack_hp_state_q[0].state = HackHpState.Idling
            self.hack_hp_state_q[0].hp_pwr_w = hp_pwr_w
            self.hack_hp_state_q[0].idu_pwr_w = idu_pwr_w
            self.hack_hp_state_q[0].odu_pwr_w = odu_pwr_w
            self.hack_hp_state_q[0].primary_pump_pwr_w = primary_pump_pwr_w
        else:
            # just update the current state
            self.hack_hp_state_q[0].hp_pwr_w = hp_pwr_w
            self.hack_hp_state_q[0].idu_pwr_w = idu_pwr_w
            self.hack_hp_state_q[0].odu_pwr_w = odu_pwr_w
            self.hack_hp_state_q[0].primary_pump_pwr_w = primary_pump_pwr_w
        
        if self.hack_hp_state_q[0].start_attempts > 1:
            send_opsgenie_scada_alert(
                name="hp-retrying",
                settings=self.settings,
                layout=self.layout,
                description=f"Heat pump has taken {self.hack_hp_state_q[0].start_attempts} to start",
                alert_team=AlertTeam.MosconeHeating
            )
    
    def enqueue_fifo_q(self, element: Any, fifo_q: Deque[Any], max_length: int = 10) -> None:
        """
        Enqueues an element into a FIFO queue represented by a deque object.

        Args:
            element (Any): The element to be enqueued.
            fifo_q (Deque[Any]): The FIFO queue represented by a deque object.
            max_length (int, optional): The maximum length of the FIFO queue. Defaults to 10.

        Returns:
            None
        """
        if len(fifo_q) >= max_length:
            fifo_q.pop()  # Remove the oldest element if queue length is equal to max_length
        fifo_q.appendleft(element)  # Add the new element at the beginning

    def _derived_process_message(self, message: Message):
        self._logger.path(
            "++Atn._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType
        )
        path_dbg = 0
        match message.Payload:
            case GtShCliAtnCmd_Maker():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.Payload.tuple.as_dict())
            case GtDispatchBoolean_Maker():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload.tuple.as_dict())
            case DBGPayload():
                path_dbg |= 0x00000004
                self._publish_to_scada(message.Payload)
            case _:
                path_dbg |= 0x00000008

        self._logger.path("--Atn._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(self, message: Message[MQTTReceiptPayload], decoded: Any):
        self._logger.path("++Atn._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name != self.SCADA_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.Payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.Payload.message.topic}]"
            )
        self.stats.add_message(decoded)
        match decoded.Payload:
            case PowerWatts():
                path_dbg |= 0x00000001
                self._process_pwr(decoded.Payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000002
                self._process_snapshot(decoded.Payload)
            case GtShStatus():
                path_dbg |= 0x00000004
                self._process_status(decoded.Payload)
            case EventBase():
                path_dbg |= 0x00000008
                self._process_event(decoded.Payload)
                if decoded.Payload.TypeName == GtShStatusEvent.__fields__["TypeName"].default:
                    path_dbg |= 0x00000010
                    self._process_status(decoded.Payload.status)
                elif decoded.Payload.TypeName == SnapshotSpaceheatEvent.__fields__["TypeName"].default:
                    path_dbg |= 0x00000020
                    self._process_snapshot(decoded.Payload.snap)
            case _:
                path_dbg |= 0x00000040
        self._logger.path("--Atn._derived_process_mqtt_message  path:0x%08X", path_dbg)

    # noinspection PyMethodMayBeStatic
    def _process_pwr(self, pwr: PowerWatts) -> None:
        self.fastpath_pwr_w = pwr.Watts
        self.hack_update_hp_pwr(from_fastpath=True)
        self.refresh_ascii_gui()
        #rich.print("Received PowerWatts")
        #rich.print(pwr)

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.prev_prev_snapshot = self.data.prev_snapshot
        self.data.prev_snapshot = self.data.latest_snapshot
        self.data.latest_snapshot = snapshot
        self.hack_update_hp_pwr()

        for node in self.my_relays:
            possible_indices = []
            for idx in range(len(snapshot.Snapshot.AboutNodeAliasList)):
                if (
                    snapshot.Snapshot.AboutNodeAliasList[idx] == node.alias
                    and snapshot.Snapshot.TelemetryNameList[idx] == TelemetryName.RelayState
                ):
                    possible_indices.append(idx)
            if len(possible_indices) != 1:
                continue
            idx = possible_indices[0]
            old_state = self.data.relay_state[node].State
            if old_state != snapshot.Snapshot.ValueList[idx]:
                self.data.relay_state[node].State = snapshot.Snapshot.ValueList[idx]
                self.data.relay_state[node].LastChangeTimeUnixMs = int(time.time() * 1000)

        self.refresh_ascii_gui()

    def _process_status(self, status: GtShStatus) -> None:
        self.data.latest_status = status
        if self.settings.save_events:
            status_file = self.status_output_dir / f"GtShStatus.{status.SlotStartUnixS}.json"
            with status_file.open("w") as f:
                f.write(str(status.as_type()))
        # self._logger.info(f"Wrote status file [{status_file}]")
        if self.settings.print_status:
            rich.print("Received GtShStatus")
            rich.print(status)

    def _process_event(self, event: EventBase) -> None:
        if self.settings.save_events:
            event_dt = pendulum.from_timestamp(event.TimeNS / 1000000000)
            event_file = (
                self.settings.paths.event_dir
                / f"{event_dt.isoformat()}.{event.TypeName}.uid[{event.MessageId}].json"
            )
            with event_file.open("w") as f:
                f.write(event.json(sort_keys=True, indent=2))

    def snap(self):
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtShCliAtnCmd_Maker(
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_id=self.layout.atn_g_node_id,
                    send_snapshot=True,
                ),
            )
        )

    def dbg(
        self,
        message_summary: int = -1,
        lifecycle: int = -1,
        comm_event: int = -1,
        command: Optional[DBGCommands | str] = None,
    ):
        self.send_dbg_to_peer(
            message_summary=message_summary,
            lifecycle=lifecycle,
            comm_event=comm_event,
            command=command
        )

    def send_dbg_to_peer(
        self,
        message_summary: int = -1,
        lifecycle: int = -1,
        comm_event: int = -1,
        command: Optional[DBGCommands | str] = None,
    ):
        if isinstance(command, str):
            command = DBGCommands(command)
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=DBGPayload(
                    Levels=LoggerLevels(
                        message_summary=message_summary,
                        lifecycle=lifecycle,
                        comm_event=comm_event,
                    ),
                    Command=command,
                ),
            )
        )

    def set_relay(self, name: str, state: bool) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtDispatchBoolean_Maker(
                    about_node_name=name,
                    to_g_node_alias=self.layout.scada_g_node_alias,
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_instance_id=self.layout.atn_g_node_instance_id,
                    relay_state=int(state),
                    send_time_unix_ms=int(time.time() * 1000),
                ),
            )
        )

    def turn_on(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, True)

    def turn_off(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, False)

    def start(self):
        if self.event_loop_thread is not None:
            raise ValueError("ERROR. start() already called once.")
        self.event_loop_thread = threading.Thread(target=asyncio.run, args=[self.run_forever()])
        self.event_loop_thread.start()

    def stop_and_join_thread(self):
        self.stop()
        if self.event_loop_thread is not None and self.event_loop_thread.is_alive():
            self.event_loop_thread.join()

    def summary_str(self) -> str:
        """Summarize results in a string"""
        s = (
            f"Atn [{self.node.alias}] total: {self._stats.num_received}  "
            f"status:{self._stats.total_received(GtShStatus_Maker.type_name)}  "
            f"snapshot:{self._stats.total_received(SnapshotSpaceheat_Maker.type_name)}"
        )
        if self._stats.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self._stats.num_received_by_topic):
                s += f"\n    {self._stats.num_received_by_topic[topic]:3d}: [{topic}]"
        if self._stats.num_received_by_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self._stats.num_received_by_type):
                s += f"\n    {self._stats.num_received_by_type[message_type]:3d}: [{message_type}]"

        return s

    def latest_simple_reading(self, node: ShNode) -> Optional[Telemetry]:
        """Provides the latest reported Telemetry value as reported in a snapshot
        message from the Scada, for a simple sensor.

        Args:
            node (ShNode): A Spaceheat Node associated to a simple sensor.

        Returns:
            Optional[int]: Returns None if no value has been reported.
            This will happen for example if the node is not associated to
            a simple sensor.
        """
        snap = self.data.latest_snapshot.Snapshot
        try:
            idx = snap.AboutNodeAliasList.index(node.alias)
        except ValueError:
            return None

        return Telemetry(Value=snap.ValueList[idx], Unit=snap.TelemetryNameList[idx])


    def refresh_ascii_gui(self) -> None:
        try:
            self.refresh_ascii_gui_implementation()
        except Exception as e:
            self._logger.error(f"ERROR in refresh_ascii_gui")
            self._logger.exception(e)

    def refresh_ascii_gui_implementation(self) -> None:
        if not self.data.prev_prev_snapshot:
            return
        ignore_alias_list = []
        snap = self.data.latest_snapshot.Snapshot
        cold_style = Style(bold=True, color="#008000")
        hot_style = Style(bold=True, color="dark_orange")
        none_text = Text("NA", style="cyan")
        # hot_ansii = "\033[31m"  # This red
        hot_ansii = "\033[36m"  # temporary for Paul's purpose screen
        # cold_ansii = "\033[34m" 
        cold_ansii = "\033[36m" # temporary for Paul's purpose screen
        prev_prev_snap = self.data.prev_prev_snapshot.Snapshot

        for j in [0,1,2]:
            flow_node = self.flow_nodes[j]
            try:
                idx = snap.AboutNodeAliasList.index(flow_node.alias)
            except:
                idx = "NA"
            # ignore_alias_list.append(idx)
    
        odu_idx = snap.AboutNodeAliasList.index(self.hp_outdoor_power_node.alias)
        ignore_alias_list.append(odu_idx)
        idu_idx = snap.AboutNodeAliasList.index(self.hp_indoor_power_node.alias)
        ignore_alias_list.append(idu_idx)

        if snap.TelemetryNameList[odu_idx] != TelemetryName.PowerW:
            raise Exception("Units problem for Outdoor Unit Power")
        if snap.TelemetryNameList[idu_idx] != TelemetryName.PowerW:
            raise Exception("Units problem for Indoor Unit Power")

        primary_idx = snap.AboutNodeAliasList.index(self.primary_pump_power_node.alias)
        ignore_alias_list.append(primary_idx)
        dist_idx = snap.AboutNodeAliasList.index(self.dist_pump_power_node.alias)
        ignore_alias_list.append(dist_idx)
        store_idx = snap.AboutNodeAliasList.index(self.store_pump_power_node.alias)
        ignore_alias_list.append(store_idx)
        pump_pwr_value = [
            snap.ValueList[primary_idx],
            snap.ValueList[dist_idx],
            snap.ValueList[store_idx],
        ]

        now = int(time.time())

        dist_pump_pwr_w = snap.ValueList[dist_idx]
        
        if self.dist_pump_pwr_state == PumpPowerState.NoFlow:
            if dist_pump_pwr_w > PUMP_OFF_THRESHOLD:
                self.dist_pump_pwr_state = PumpPowerState.Flow
                tt = [PumpPowerState.Flow, dist_pump_pwr_w, now]
                self.enqueue_fifo_q(tt, self.dist_pump_pwr_state_q)
        elif self.dist_pump_pwr_state == PumpPowerState.Flow:
            if dist_pump_pwr_w < PUMP_OFF_THRESHOLD:
                self.dist_pump_pwr_state = PumpPowerState.NoFlow
                tt = [PumpPowerState.NoFlow, dist_pump_pwr_w, now]
                self.enqueue_fifo_q(tt, self.dist_pump_pwr_state_q)

        # store_temp_idx = {1: {}, 2: {}, 3: {}, 4: {}}
        # store_temp_f = {1: {}, 2: {}, 3: {}, 4: {}}
        #
        # for j in [1,2,3]:
        #     store_temp_idx[1][j] = snap.AboutNodeAliasList.index(self.store[j].t1.alias)
        #     store_temp_idx[2][j] = snap.AboutNodeAliasList.index(self.store[j].t2.alias)
        #     store_temp_idx[3][j] = snap.AboutNodeAliasList.index(self.store[j].t3.alias)
        #     store_temp_idx[4][j] = snap.AboutNodeAliasList.index(self.store[j].t4.alias)
        #
        # for i in range(1,5):
        #     for j in range(1,4):
        #         ignore_alias_list.append(store_temp_idx[i][j])
        #         store_temp_f[i][j] = 9/5 * (snap.ValueList[store_temp_idx[i][j]] / 1000) + 32

        store_temp_f = defaultdict(dict)
        for depth in [1, 2, 3, 4]:
            for tank in [1, 2, 3]:
                alias = getattr(self.store[tank], f"t{depth}").alias
                try:
                    node_idx = snap.AboutNodeAliasList.index(alias)
                    ignore_alias_list.append(node_idx)
                    store_temp_f[depth][tank] =  9/5 * (snap.ValueList[node_idx] / 1000) + 32
                except ValueError:
                    ...


        # buff_idx = {}
        #
        # buff_idx[1] = snap.AboutNodeAliasList.index(self.buffer.t1.alias)
        # buff_idx[2] = snap.AboutNodeAliasList.index(self.buffer.t2.alias)
        # buff_idx[3] = snap.AboutNodeAliasList.index(self.buffer.t3.alias)
        # buff_idx[4] = snap.AboutNodeAliasList.index(self.buffer.t4.alias)
        #
        # buff_temp_f = {}
        # for j in range(1,5):
        #     assert snap.TelemetryNameList[buff_idx[j]] == TelemetryName.WaterTempCTimes1000
        #     ignore_alias_list.append(buff_idx[j])
        #     buff_temp_f[j] = 9/5 * (snap.ValueList[buff_idx[j]] / 1000) + 32
        buff_temp_f = {}
        for depth in [1, 2, 3, 4]:
            alias = getattr(self.buffer, f"t{depth}").alias
            try:
                node_idx = snap.AboutNodeAliasList.index(alias)
                ignore_alias_list.append(node_idx)
                assert snap.TelemetryNameList[node_idx] == TelemetryName.WaterTempCTimes1000
                buff_temp_f[depth] =  9/5 * (snap.ValueList[node_idx] / 1000) + 32
            except ValueError:
                ...

        hp_lwt_idx = snap.AboutNodeAliasList.index(self.hp_lwt_temp_node.alias)
        ignore_alias_list.append(hp_lwt_idx)
        hp_ewt_idx = snap.AboutNodeAliasList.index(self.hp_ewt_temp_node.alias)
        ignore_alias_list.append(hp_ewt_idx)
        dist_swt_idx = snap.AboutNodeAliasList.index(self.dist_swt_temp_node.alias)
        ignore_alias_list.append(dist_swt_idx)
        dist_rwt_idx = snap.AboutNodeAliasList.index(self.dist_rwt_temp_node.alias)
        ignore_alias_list.append(dist_rwt_idx)
        buffer_hot_idx = snap.AboutNodeAliasList.index(self.buffer_hot_pipe_temp_node.alias)
        ignore_alias_list.append(buffer_hot_idx)
        buffer_cold_idx = snap.AboutNodeAliasList.index(self.buffer_cold_pipe_temp_node.alias)
        ignore_alias_list.append(buffer_cold_idx)
        store_hot_idx = snap.AboutNodeAliasList.index(self.store_hot_pipe_temp_node.alias)
        ignore_alias_list.append(store_hot_idx)
        store_cold_idx = snap.AboutNodeAliasList.index(self.store_cold_pipe_temp_node.alias)
        ignore_alias_list.append(store_cold_idx)

        stat_temp_idx = {}
        stat_set_f = {}
        stat_wall_temp_f = {}
        stat_temp_f = {}
        for j in self.stat.keys():
            if self.stat[j].gw_temp is not None:
                stat_temp_idx[j] = snap.AboutNodeAliasList.index(self.stat[j].gw_temp.alias)
                ignore_alias_list.append(stat_temp_idx[j])
                if snap.TelemetryNameList[stat_temp_idx[j]] != TelemetryName.AirTempCTimes1000:
                    raise Exception(f"Wrong TelemetryName for {self.stat[1].gw_temp.alias}. Use AirTempCTimes1000")
                stat_temp_centigrade = snap.ValueList[stat_temp_idx[j]] / 1000
                stat_temp_f[j] = (stat_temp_centigrade  * 9/5) + 32

            try:
                stat_set_idx = snap.AboutNodeAliasList.index(self.stat[j].set.alias)
                ignore_alias_list.append(stat_set_idx)
                stat_set_f[j] = snap.ValueList[stat_set_idx] / 1000
                if snap.TelemetryNameList[stat_set_idx] != TelemetryName.AirTempFTimes1000:
                    raise Exception(f"Wrong TelemetryName for {self.stat[1].set.alias}. Use AirTempFTimes1000")
            except ValueError:
                ...

            try:
                stat_wall_temp_idx = snap.AboutNodeAliasList.index(self.stat[j].wall_unit_temp.alias)
                ignore_alias_list.append(stat_wall_temp_idx)
                stat_wall_temp_f[j] = snap.ValueList[stat_wall_temp_idx] / 1000
                if snap.TelemetryNameList[stat_wall_temp_idx] != TelemetryName.AirTempFTimes1000:
                    raise Exception(f"Wrong TelemetryName for {self.stat[1].wall_unit_temp.alias}. Use AirTempFTimes1000")
            except ValueError:
                ...

        if snap.TelemetryNameList[hp_lwt_idx] != TelemetryName.WaterTempCTimes1000:
            raise Exception("Wrong TelemetryName for hp lwt")
        if snap.TelemetryNameList[dist_swt_idx] != TelemetryName.WaterTempCTimes1000:
            raise Exception("Wrong TelemetryName for hp swt")
        hp_lwt_centigrade = snap.ValueList[hp_lwt_idx] / 1000
        hp_ewt_centigrade = snap.ValueList[hp_ewt_idx] / 1000
        dist_swt_centigrade = snap.ValueList[dist_swt_idx] / 1000
        dist_rwt_centigrade = snap.ValueList[dist_rwt_idx] / 1000
        buffer_hot_centigrade = snap.ValueList[buffer_hot_idx] / 1000
        buffer_cold_centigrade = snap.ValueList[buffer_cold_idx] / 1000
        store_hot_centigrade = snap.ValueList[store_hot_idx] / 1000
        store_cold_centigrade = snap.ValueList[store_cold_idx] / 1000

        hp_lwt_f = (hp_lwt_centigrade * 9/5) + 32
        hp_ewt_f = (hp_ewt_centigrade * 9/5) + 32
        dist_swt_f = (dist_swt_centigrade * 9/5) + 32
        dist_rwt_f = (dist_rwt_centigrade * 9/5) + 32
        buffer_hot_f = (buffer_hot_centigrade * 9/5) + 32
        buffer_cold_f = (buffer_cold_centigrade * 9/5) + 32
        store_hot_f = (store_hot_centigrade * 9/5) + 32
        store_cold_f = (store_cold_centigrade * 9/5) + 32

        ## PRINT THE STUFF THAT IS NOT IN THE TABLES
        snapshot = self.data.latest_snapshot
        odds_end_str = "Odds and Ends:\n"
        for j in range(len(snapshot.Snapshot.AboutNodeAliasList)):
            if j not in ignore_alias_list:
                telemetry_name = snapshot.Snapshot.TelemetryNameList[j]
                if (telemetry_name == TelemetryName.WaterTempCTimes1000
                or telemetry_name == TelemetryName.WaterTempCTimes1000.value
                or telemetry_name == TelemetryName.AirTempCTimes1000
                or telemetry_name == TelemetryName.AirTempCTimes1000.value
                        ):
                    centigrade = snapshot.Snapshot.ValueList[j] / 1000
                    if self.settings.c_to_f:
                        fahrenheit = (centigrade * 9/5) + 32
                        extra = f"{fahrenheit:5.2f}\u00b0F"
                    else:
                        extra = f"{centigrade:5.2f}\u00b0C"
                else:
                    extra = (
                        f"{snapshot.Snapshot.ValueList[j]} "
                        f"{snapshot.Snapshot.TelemetryNameList[j].value}"
                    )
                odds_end_str += f"  {snapshot.Snapshot.AboutNodeAliasList[j]}: {extra}\n"
        # odds_end_str += f"snapshot is None:{snapshot is None}\n"
        # odds_end_str += "json.dumps(snapshot.asdict()):\n"
        # odds_end_str += json.dumps(snapshot.asdict(), sort_keys=True, indent=2)
        # odds_end_str += "\n"
        self._logger.warning(odds_end_str)
        # rich.print(snapshot)
        
        est = pendulum.from_timestamp(snap.ReportTimeUnixMs / 1000).in_tz('America/New_York')
        print(f"{est.format('YYYY-MM-DD HH:mm:ss:SSS')}:")

        stat_table = Table()
        stat_table.add_column("Stats", header_style="bold")
        stat_table.add_column("Setpt", header_style="bold")
        stat_table.add_column("HW Temp", header_style="bold")
        stat_table.add_column("GW Temp", header_style="bold")

        if len(self.dist_pump_pwr_state_q)> 0:
            until = int(time.time())
            t = self.dist_pump_pwr_state_q
            stat_table.add_column("Heat Call", header_style="bold")
            for j in range(min(6,len(t))):
                start_s =  t[j][2]
                minutes = int((until - start_s)/60)
                if t[j][0] == PumpPowerState.Flow:
                    stat_table.add_column(f"On {minutes}", header_style=hot_style)
                else:
                    stat_table.add_column(f"Off {minutes}", header_style=cold_style)
                until = start_s

        
        # TODO: DISAMBIGUATE HEAT CALLS BETWEEN ZONES WHEN WE HAVE MULTIPLE ZONES
        for j in self.stat.keys():
            if j in stat_set_f:
                stat_set_f_str = f"{round(stat_set_f[j],1)}\u00b0F"
            else:
                stat_set_f_str = "---"
            if j in stat_wall_temp_f:
                stat_wall_temp_f_str = f"{round(stat_wall_temp_f[j],1)}\u00b0F"
            else:
                stat_wall_temp_f_str = "---"
            stat_row = [
                f"{self.stat[j].display_name}",
                stat_set_f_str,
                stat_wall_temp_f_str,
            ]
            if j in stat_temp_f.keys():
                stat_row.append(f"{round(stat_temp_f[j],1)}\u00b0F")
            if len(self.dist_pump_pwr_state_q)> 0:
                until = int(time.time())
                t = self.dist_pump_pwr_state_q
                start_times = []
                for j in range(min(6,len(t))):
                    start_s =  t[j][2]
                    start_times.append(pendulum.from_timestamp(start_s, tz='America/New_York').format('HH:mm'))
                    minutes = int((until - start_s)/60)
                    until = start_s
                stat_row.append("Start")
                stat_row.extend(start_times)
            stat_table.add_row(*stat_row)

        import rich
        rich.print(stat_table)
        
        power_table = Table()

        power_table.add_column("HP Power", header_style="bold")
        power_table.add_column("kW", header_style="bold")
        power_table.add_column("X", header_style="bold dark_orange", style="dark_orange")
        power_table.add_column("Pump", header_style="bold")
        power_table.add_column("Gpm", header_style="bold")
        power_table.add_column("Pwr (W)", header_style="bold")
        power_table.add_column("HP State", header_style="bold dark_orange", style="bold dark_orange")

        extra_cols = min(len(self.hack_hp_state_q),5)
        for i in range(extra_cols):
            power_table.add_column(f"{self.hack_hp_state_q[i].state.value}", header_style="bold")
        

        hp_pwr_w_str = f"{round(self.hack_hp_state_q[0].hp_pwr_w / 1000, 2)}"
        if self.hack_hp_state_q[0].idu_pwr_w is None:
            idu_pwr_w_str = none_text
            odu_pwr_w_str = none_text
        else:   
            idu_pwr_w_str = f"{round(self.hack_hp_state_q[0].idu_pwr_w / 1000, 2)}"
            odu_pwr_w_str = f"{round(self.hack_hp_state_q[0].odu_pwr_w / 1000, 2)}"
    
        pump_pwr_str = {}
        gpm_str = {}
        for j in [0,1,2]:
            if pump_pwr_value[j] < PUMP_OFF_THRESHOLD:
                pump_pwr_str[j]  = "OFF"
            else:
                pump_pwr_str[j] = f"{round(pump_pwr_value[j],2)}"
            flow_node = self.flow_nodes[j]
            try:
                idx = snap.AboutNodeAliasList.index(flow_node.alias)
                if snap.TelemetryNameList[idx] != TelemetryName.GallonsTimes100:
                    raise Exception('Error in units. Expect TelemetryName.GallonsTimes100')
                delta_gallons = (snap.ValueList[idx] - prev_prev_snap.ValueList[idx] )/ 100
                delta_min = (snap.ReportTimeUnixMs  - prev_prev_snap.ReportTimeUnixMs)/ 60_000
                speed = delta_gallons / delta_min
                if speed > 20:
                    gpm_str[j] = "BAD"
                else:
                    gpm_str[j] = f"{round(speed,1)}"
            except:
                gpm_str[j] = "NA"
            
        row_1 = ["Hp Total", hp_pwr_w_str, "x", "Primary", gpm_str[0], pump_pwr_str[0], "Started"]
        row_2 = ["Outdoor", odu_pwr_w_str, "x", "Dist", gpm_str[1], pump_pwr_str[1], "Tries"]
        row_3 = ["Indoor", idu_pwr_w_str, "x", "Store", gpm_str[2], pump_pwr_str[2], "PumpPwr"]
        for i in range(extra_cols):
            row_1.append(f"{pendulum.from_timestamp(self.hack_hp_state_q[i].state_start_s, tz='America/New_York').format('HH:mm')}")
            if (self.hack_hp_state_q[i].state == HackHpState.Idling
                or self.hack_hp_state_q[i].state == HackHpState.Trying):
                row_2.append(f"{self.hack_hp_state_q[i].start_attempts}")
            else:
                row_2.append(f"")
            row_3.append(f"{self.hack_hp_state_q[i].primary_pump_pwr_w} W")
            
        power_table.add_row(*row_1)
        power_table.add_row(*row_2)
        power_table.add_row(*row_3)
    
        rich.print(power_table)
        
        hp_lwt_ansii = hot_ansii
        hp_ewt_ansii = cold_ansii
        if hp_lwt_f < hp_ewt_f - 1:
            hp_lwt_ansii = cold_ansii
            hp_ewt_ansii = hot_ansii
        if hp_lwt_f < 100:
            hp_lwt_f_str = f" {hp_lwt_ansii}{round(hp_lwt_f,1)}\u00b0F\033[0m"
        else:
            hp_lwt_f_str = f"{hp_lwt_ansii}{round(hp_lwt_f,1)}\u00b0F\033[0m"
        if hp_ewt_f < 100:
            hp_ewt_f_str = f" {hp_ewt_ansii}{round(hp_ewt_f,1)}\u00b0F\033[0m"
        else:
            hp_ewt_f_str = f"{hp_ewt_ansii}{round(hp_ewt_f,1)}\u00b0F\033[0m"
        
        dist_swt_ansii = hot_ansii
        dist_rwt_ansii = cold_ansii
        
        if dist_swt_f < dist_rwt_f - 1:
            dist_swt_ansii = cold_ansii
            dist_rwt_ansii = hot_ansii
        if dist_swt_f < 100:
            dist_swt_f_str = f" {dist_swt_ansii}{round(dist_swt_f,1)}\u00b0F\033[0m"
        else:
            dist_swt_f_str = f"{dist_swt_ansii}{round(dist_swt_f,1)}\u00b0F\033[0m"
        if dist_rwt_f < 100:
            dist_rwt_f_str = f" {dist_rwt_ansii}{round(dist_rwt_f,1)}\u00b0F\033[0m"
        else:
            dist_rwt_f_str = f"{dist_rwt_ansii}{round(dist_rwt_f,1)}\u00b0F\033[0m"
        
        buffer_hot_ansii = hot_ansii
        buffer_cold_ansii = cold_ansii
        if buffer_hot_f < buffer_cold_f - 1:
            buffer_hot_ansii = cold_ansii
            buffer_cold_ansii = hot_ansii
        
        if buffer_hot_f < 100:
            buffer_hot_f_str = f" {buffer_hot_ansii}{round(buffer_hot_f,1)}\u00b0F\033[0m"
        else:
            buffer_hot_f_str = f"{buffer_hot_ansii}{round(buffer_hot_f,1)}\u00b0F\033[0m"
        if buffer_cold_f < 100:
            buffer_cold_f_str = f" {buffer_cold_ansii}{round(buffer_cold_f,1)}\u00b0F\033[0m"
        else:
            buffer_cold_f_str = f"{buffer_cold_ansii}{round(buffer_cold_f,1)}\u00b0F\033[0m"
        
        store_hot_ansii = hot_ansii
        store_cold_ansii = cold_ansii
        if store_hot_f < store_cold_f - 1:
            store_hot_ansii = cold_ansii
            store_cold_ansii = hot_ansii
        
        if store_hot_f < 100:
            store_hot_f_str = f" {store_hot_ansii}{round(store_hot_f,1)}\u00b0F\033[0m"
        else:
            store_hot_f_str = f"{store_hot_ansii}{round(store_hot_f,1)}\u00b0F\033[0m"
        if store_cold_f < 100:
            store_cold_f_str = f" {store_cold_ansii}{round(store_cold_f,1)}\u00b0F\033[0m"
        else:
            store_cold_f_str = f"{store_cold_ansii}{round(store_cold_f,1)}\u00b0F\033[0m"

        buff_temp_f_str = {}
        for depth in range(1,5):
            if depth in buff_temp_f:
                if buff_temp_f[depth] < 100:
                    s = f" {round(buff_temp_f[depth],1)}\u00b0F"
                else:
                    s = f"{round(buff_temp_f[depth],1)}\u00b0F"
            else:
                s = "  ---  "
            buff_temp_f_str[depth] = s

        # store_temp_f_str = {1: {}, 2: {}, 3: {}, 4: {}}
        store_temp_f_str = defaultdict(dict)
        for depth in range(1,5):
            for tank in range(1,4):
                if depth in store_temp_f and tank in store_temp_f[depth]:
                    if store_temp_f[depth][tank] < 100:
                        s = f" {round(store_temp_f[depth][tank], 1)}\u00b0F"
                    else:
                        s = f"{round(store_temp_f[depth][tank], 1)}\u00b0F"
                else:
                    s = "  ---  "
                store_temp_f_str[depth][tank] = s
        
        
        hack_hp_state = self.hack_hp_state_q[0]
        if hack_hp_state.state == HackHpState.Heating:
            heating = True
        else:
            heating = False
        
        if heating is True:
            hp_health_comment_1 = ""
            hp_health_comment_2 = ""
        else:
            hp_health_comment_1 = f"{hack_hp_state.state.value}."
            last_heating = next((x for x in self.hack_hp_state_q if x.state == HackHpState.Heating), None)
            hp_health_comment_2 = ""
            if last_heating is not None:
                if last_heating.state_end_s:
                    hp_health_comment_2 += f"Last time heating: {pendulum.from_timestamp(last_heating.state_end_s, tz='America/New_York').format('HH:mm')}. "
            if hack_hp_state.start_attempts == 1:
                hp_health_comment_2 += f"1 start attempt."
            elif hack_hp_state.start_attempts > 1:
                hp_health_comment_2 += f"{hack_hp_state.start_attempts} start attempts."
        atn_alias = self.layout.atn_g_node_alias
        short_name = atn_alias.split(".")[-1]
        print(f"""{short_name}:
                                 {hp_lwt_ansii}HP LWT\033[0m   ┏━━━━━┓   {hp_health_comment_1}
                               ┏━{hp_lwt_f_str}━━┃ HP  ┃   {hp_health_comment_2}
  {buffer_hot_ansii}Buff Hot\033[0m ━━┓                 ┃    ┏─────┃     ┃   Lift: {round(hp_lwt_f - hp_ewt_f,1)}\u00b0F
   {buffer_hot_f_str}   ┃                 ┃ {hp_ewt_ansii}HP EWT\033[0m   └─────┘
 ┏━━━━━━━━━┓ ▼                 ┃ {hp_ewt_f_str}
 ┃  Buffer ┃━━━━━━━━━┳━ ISO ━━─┴─━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ 
 ┡━━━━━━━━━┩         ┃              │         ┏━━━━━━━━━┓   ┏━━━━━━━━━┓   ┏━━━━━━━━━┓    ┃
 │ {buff_temp_f_str[1]} │       {dist_swt_ansii}Dist FWT\033[0m         │         ┃  Tank3  ┃   ┃  Tank2  ┃   ┃  Tank1  ┃    ┃
 │ {buff_temp_f_str[2]} │       {dist_swt_f_str}          │         ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━┓ ┡━━━━━━━━━┩━━━{store_hot_f_str}
 │ {buff_temp_f_str[3]} │         ┃              │         │ {store_temp_f_str[1][3]} │ │ │ {store_temp_f_str[1][2]} │ │ │ {store_temp_f_str[1][1]} │
 │ {buff_temp_f_str[4]} │────┓    ┃              │         │ {store_temp_f_str[2][3]} │ │ │ {store_temp_f_str[2][2]} │ │ │ {store_temp_f_str[2][1]} │
 └─────────┘ ▲  │    ┃              │         │ {store_temp_f_str[3][3]} │ │ │ {store_temp_f_str[3][2]} │ │ │ {store_temp_f_str[3][1]} │
  {buffer_cold_ansii}Buff Cold\033[0m  │  ┡────┃──────────────┴─{store_cold_f_str}─│ {store_temp_f_str[4][3]} │ └━│ {store_temp_f_str[4][2]} │ └━│ {store_temp_f_str[4][1]} │
   {buffer_cold_f_str} ──┘  │    ┃                        └─────────┘   └─────────┘   └─────────┘
            {dist_rwt_ansii}Dist RWT\033[0m ┃                           
            {dist_rwt_f_str}  ┃  Emitter \u0394 = {round(dist_swt_f - dist_rwt_f,1)}\u00b0F 
""") 
