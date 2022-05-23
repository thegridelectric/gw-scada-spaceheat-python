
import paho.mqtt.client as mqtt
import time
import json
from typing import List
from messages.gt_telemetry_1_0_0 import \
    Gt_Telemetry_1_0_0, TelemetryName

delta_ms = []
payloads = []
def on_message(client, userdata, message):
    payload_dict = json.loads((str(message.payload.decode("utf-8"))))
    payload = Gt_Telemetry_1_0_0.create_payload_from_camel_dict(payload_dict)
    time_delta_ms = int(time.time()*1000) - payload.ScadaReadTimeUnixMs
    payloads.append(payload)
    delta_ms.append(time_delta_ms)

mqttBroker ="mqtt.eclipseprojects.io"

client = mqtt.Client("HeatScada")
client.connect(mqttBroker) 

client.loop_start()

client.subscribe("gt.telemetry.100")
client.on_message=on_message 

time.sleep(15)
client.loop_stop()
print("Average delta_ms", round(sum(delta_ms)/len(delta_ms)) )