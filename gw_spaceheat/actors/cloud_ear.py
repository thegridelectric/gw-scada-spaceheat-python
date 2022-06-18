
import csv
import time
import uuid
from typing import List

import helpers
import load_house
import pendulum
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus_Maker, GtShSimpleStatus)


from actors.cloud_ear_base import CloudEarBase
from actors.utils import QOS, Subscription

atn_ender = settings.ATN_G_NODE_ALIAS.replace(".", "_")
# OUT_STUB = f'/Users/jess/Google Drive/My Drive/GridWorks/Projects/Internal Maine Heat Pilot/SCADA/data/{atn_ender}'
OUT_STUB = atn_ender


class CloudEar(CloudEarBase):
    def __init__(self, write_to_csv=False):
        self.write_to_csv = write_to_csv
        super(CloudEar, self).__init__()
        self.total_power_w = 0
        if self.write_to_csv:
            adder = str(uuid.uuid4()).split('-')[1]
            self.out_telemetry = f'{OUT_STUB}_{adder}.csv'
            self.screen_print(f"writing output headers ending in {adder}")
            with open(self.out_telemetry, 'w') as outfile:
                write = csv.writer(outfile, delimiter=',')
                write.writerow(['TimeUtc', 'TimeUnixS', 'ShNodeAlias', 'Value', 'TelemetryName'])
        self.load_sh_nodes()
        self.screen_print(f'Initialized {self.__class__}')

    def load_sh_nodes(self):
        load_house.load_all()

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GtShSimpleStatus_Maker.type_alias}',
                             Qos=QOS.AtLeastOnce)]

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GtSpaceheatStatus):
            self.gt_spaceheat_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.total_power_w = payload.Power

    def log_csv(self, payload: GtSpaceheatStatus):
        new_readings = []
        sync_status = payload.SyncStatusList[0]
        for sync_status in payload.SyncStatusList:
            sync_status.ShNodeAlias
            record_time_unix_s = sync_status.FirstReadTimeUnixS
            for i in range(len(sync_status.ValueList)):
                record_time_unix_s += i * sync_status.SamplePeriodS
                t = pendulum.from_timestamp(record_time_unix_s)
                new_readings.append([t.strftime("%Y-%m-%d %H:%M:%S"),
                                    record_time_unix_s,
                                    sync_status.ShNodeAlias,
                                    sync_status.ValueList[i],
                                    sync_status.TelemetryName.value])

        self.screen_print("appending output")
        with open(self.out_telemetry, 'a') as outfile:
            write = csv.writer(outfile, delimiter=',')
            for row in new_readings:
                write.writerow(row)

    def gt_spaceheat_status_received(self, from_node: ShNode, payload: GtSpaceheatStatus):
        if self.write_to_csv:
            self.log_csv(payload=payload)
        self.latest_status_payload = payload

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)
