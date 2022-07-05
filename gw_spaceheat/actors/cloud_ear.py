import csv
import time
import uuid
from typing import List

import pendulum

import settings
from actors.cloud_base import CloudBase
from actors.utils import QOS, Subscription, responsive_sleep
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker

from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean_maker import (
    GtDispatchBoolean,
    GtDispatchBoolean_Maker,
)
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import (
    GtShCliScadaResponse_Maker,
)
from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus, GtShStatus_Maker

OUT_STUB = "output/status"


class CloudEar(CloudBase):
    def __init__(self, out_stub=OUT_STUB, logging_on=False):
        if out_stub is None:
            self.write_to_csv = False
        else:
            self.write_to_csv = True
        super(CloudEar, self).__init__(logging_on=logging_on)
        self.log_csv = f"output/debug_logs/ear_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.load_sh_nodes()
        self.csv_rows = []
        if self.write_to_csv:
            adder = str(uuid.uuid4()).split("-")[1]
            atn_ender = settings.ATN_G_NODE_ALIAS.replace(".", "_")
            self.out_telemetry = f"{out_stub}/{atn_ender}_{adder}.csv"
            self.screen_print(f"writing output headers ending in {adder}")
            with open(self.out_telemetry, "w") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(
                    [
                        "TimeUtc",
                        "TimeUnixS",
                        "Ms",
                        "About",
                        "Value",
                        "TelemetryName",
                        "Sensor",
                        "RelayCmd",
                        "CmdFrom",
                    ]
                )
        self.screen_print(f"Initialized {self.__class__}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GsPwr_Maker.type_alias}", Qos=QOS.AtMostOnce
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GtShStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GtShCliScadaResponse_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, from_node: ShNode, payload):
        self.send_to_kafka(payload=payload)
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GtShStatus):
            self.gt_sh_status_received(from_node, payload)
        elif isinstance(payload, GtDispatchBoolean):
            self.gt_dispatch_received(from_node, payload)

    def send_to_kafka(self, payload):
        # topic = f"{self.scada_g_node_alias}/{payload.TypeAlias}"
        # publish payload.as_type() to topic in Kafka
        pass

    def gt_dispatch_received(self, from_node: ShNode, payload: GtDispatchBoolean):
        if self.write_to_csv:
            self.log_dispatch_cmds_to_csv(from_node, payload)

    def log_dispatch_cmds_to_csv(self, from_node: ShNode, payload: GtDispatchBoolean):
        time_unix_ms = payload.SendTimeUnixMs
        int_time_unix_s = int(time_unix_ms / 1000)
        ms = int(time_unix_ms) % 1000
        time_utc = pendulum.from_timestamp(int_time_unix_s)
        row = [
            time_utc.strftime("%Y-%m-%d %H:%M:%S"),
            int_time_unix_s,
            ms,
            payload.ShNodeAlias,
            "",
            "",
            "",
            payload.RelayState,
            from_node.alias,
        ]
        self.csv_rows.append(row)

    def gt_sh_status_received(self, from_node: ShNode, payload: GtShStatus):
        self.screen_print(f"Consider adding from_node {from_node} or its g node alias to log?")
        if self.write_to_csv:
            self.log_status_csv(payload=payload)

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        pass

    def log_status_csv(self, payload: GtShStatus):
        for status in payload.SimpleTelemetryList:
            for i in range(len(status.ValueList)):
                time_unix_ms = status.ReadTimeUnixMsList[i]
                int_time_unix_s = int(time_unix_ms / 1000)
                ms = int(time_unix_ms) % 1000
                time_utc = pendulum.from_timestamp(int_time_unix_s)
                self.csv_rows.append(
                    [
                        time_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        int_time_unix_s,
                        ms,
                        status.ShNodeAlias,
                        status.ValueList[i],
                        status.TelemetryName.value,
                    ]
                )

        for status in payload.MultipurposeTelemetryList:
            for i in range(len(status.ValueList)):
                time_unix_ms = status.ReadTimeUnixMsList[i]
                int_time_unix_s = int(time_unix_ms / 1000)
                ms = int(time_unix_ms) % 1000
                time_utc = pendulum.from_timestamp(int_time_unix_s)
                self.csv_rows.append(
                    [
                        time_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        int_time_unix_s,
                        ms,
                        status.AboutNodeAlias,
                        status.ValueList[i],
                        status.TelemetryName.value,
                        status.SensorNodeAlias,
                    ]
                )

        for status in payload.BooleanactuatorCmdList:
            for i in range(len(status.RelayStateCommandList)):
                time_unix_ms = status.CommandTimeUnixMsList[i]
                int_time_unix_s = int(time_unix_ms / 1000)
                ms = int(time_unix_ms) % 1000
                time_utc = pendulum.from_timestamp(int_time_unix_s)
                self.csv_rows.append(
                    [
                        time_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        int_time_unix_s,
                        ms,
                        status.ShNodeAlias,
                        "",
                        "",
                        "",
                        status.RelayStateCommandList[i],
                        status.ShNodeAlias,
                    ]
                )

        self.screen_print(f"appending output to {self.out_telemetry.split('_')[-1]}")
        now_utc = pendulum.from_timestamp(int(time.time()))
        self.screen_print(f'{now_utc.strftime("%Y-%m-%d %H:%M:%S")}')
        rows = sorted(self.csv_rows, key=lambda x: x[1] * 1000 + x[2])
        with open(self.out_telemetry, "a") as outfile:
            write = csv.writer(outfile, delimiter=",")
            for row in rows:
                write.writerow(row)
        self.csv_rows = []

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            responsive_sleep(self, 10)

    def screen_print(self, note):
        header = "Cloud Ear: "
        print(header + note)
