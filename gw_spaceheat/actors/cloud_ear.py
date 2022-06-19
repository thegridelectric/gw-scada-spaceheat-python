import csv
import time
import uuid
from typing import List

import helpers
import pendulum
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus_Maker,
    GtShSimpleStatus,
)


from actors.cloud_base import CloudBase
from actors.utils import QOS, Subscription

atn_ender = settings.ATN_G_NODE_ALIAS.replace(".", "_")
# OUT_STUB = f'/Users/jess/Google Drive/My Drive/GridWorks/Projects/Internal Maine Heat Pilot/SCADA/data/{atn_ender}'
OUT_STUB = f"output/status/{atn_ender}"


class CloudEar(CloudBase):
    def __init__(self, write_to_csv=False, logging_on=False):
        self.write_to_csv = write_to_csv
        super(CloudEar, self).__init__(logging_on=logging_on)
        self.log_csv = f"output/debug_logs/ear_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.load_sh_nodes()
        if self.write_to_csv:
            adder = str(uuid.uuid4()).split("-")[1]
            self.out_telemetry = f"{OUT_STUB}_{adder}.csv"
            self.screen_print(f"writing output headers ending in {adder}")
            with open(self.out_telemetry, "w") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(["TimeUtc", "TimeUnixS", "Ms", "Alias", "Value", "TelemetryName"])
        self.screen_print(f"Initialized {self.__class__}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GsPwr_Maker.type_alias}", Qos=QOS.AtMostOnce
            ),
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GtShSimpleStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias["a.s"]:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GtShSimpleStatus):
            self.gt_sh_simple_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gt_sh_simple_status_received(self, from_node: ShNode, payload: GtShSimpleStatus):
        self.screen_print(f"Consider adding from_node {from_node} or its g node alias to log?")
        if self.write_to_csv:
            self.log_status_csv(payload=payload)

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.screen_print(f"Got {payload} from {from_node}. Need to log!")

    def log_status_csv(self, payload: GtShSimpleStatus):
        new_readings = []
        for single in payload.SimpleSingleStatusList:
            for i in range(len(single.ValueList)):
                time_unix_ms = single.ReadTimeUnixMsList[i]
                int_time_unix_s = int(time_unix_ms / 1000)
                ms = int(time_unix_ms) % 1000
                time_utc = pendulum.from_timestamp(int_time_unix_s)
                new_readings.append(
                    [
                        time_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        int_time_unix_s,
                        ms,
                        single.ShNodeAlias,
                        single.ValueList[i],
                        single.TelemetryName.value,
                    ]
                )

        self.screen_print(f"appending output to {self.out_telemetry.split('_')[-1]}")
        now_utc = pendulum.from_timestamp(int(time.time()))
        self.screen_print(f'{now_utc.strftime("%Y-%m-%d %H:%M:%S")}')
        with open(self.out_telemetry, "a") as outfile:
            write = csv.writer(outfile, delimiter=",")
            for row in new_readings:
                write.writerow(row)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(10)

    def screen_print(self, note):
        header = "Cloud Ear: "
        print(header + note)
