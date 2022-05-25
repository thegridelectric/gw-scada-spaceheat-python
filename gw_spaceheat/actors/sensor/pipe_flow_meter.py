
import json
import paho.mqtt.client as mqtt 
import time

from actors.sensor.sensor_base import SensorBase

from data_classes.components.sensor_component import SensorComponent
from data_classes.cacs.sensor_cac import SensorCac
from data_classes.sh_node import ShNode
from data_classes.sensor_type_static import WATER_FLOW_METER
from data_classes.sh_node_role_static import SENSOR
from schema.gt.gt_telemetry.gt_telemetry_1_0_0_base import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_1_0_0_maker import GtTelemetry100, GtTelemetry100_Maker


class Pipe_Flow_Meter(SensorBase):
    def __init__(self, node: ShNode):
        super(Pipe_Flow_Meter, self).__init__(node=node)   
        self.water_flow_gpm = 0
        self.screen_print('hi')
        self.consume_thread.start()

    def publish(self):
        self.water_flow_gpm += 100
        self.water_flow_gpm = self.water_flow_gpm % 3000
        payload = GtTelemetry100_Maker(name=TelemetryName.WATER_FLOW_GPM_TIMES_100.value,
                        value=int(self.water_flow_gpm*100),
                        scada_read_time_unix_ms=int(time.time()*1000)).type
        self.publish_gt_telemetry_1_0_0(payload)
        
    def consume(self):
        pass