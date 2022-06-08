
import time
from actors.sensor.sensor_base import SensorBase
from data_classes.sh_node import ShNode
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_base import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import \
    GtTelemetry101_Maker


class PipeFlowMeter(SensorBase):
    def __init__(self, node: ShNode):
        super(PipeFlowMeter, self).__init__(node=node)   
        self.water_flow_gpm = 0
        self.screen_print('hi')
        self.consume_thread.start()

    def publish(self):
        self.water_flow_gpm += 100
        self.water_flow_gpm = self.water_flow_gpm % 3000
        payload = GtTelemetry101_Maker(name=TelemetryName.WATER_FLOW_GPM_TIMES_100.value,
                                       value=int(self.water_flow_gpm * 100),
                                       scada_read_time_unix_ms=int(time.time() * 1000)).type
        self.publish_gt_telemetry_1_0_1(payload)
        
    def consume(self):
        pass