#Debug mosquitto

Publish is failing after a sending 20 messages. This is independent of the broker used.

Here is how to replicate the failure.
Follow directions in this folder README.md to set up the development environment using the free mqtt broker mqtt.eclipseprojects.io

Run  `python try_temp_sensor.py`

It'll start out like this:

a.tank.temp0: Trying to publish
log: Sending PUBLISH (d0, q1, r0, m1), 'b'a.tank.temp0/gt.telemetry.101'', ... (116 bytes)

(repeating about once a second)
and then after a while all you will see is this:

a.tank.temp0: Trying to publish
a.tank.temp0: Trying to publish
a.tank.temp0: Trying to publish


In contrast, `python publish.py` sends a message of the same format works fine


The primary mqtt in the code is in `actors/actor_base.py`. The publishing happens in `actors/sensor_base.py` with these lines:

def publish_gt_telemetry_1_0_1(self, payload: GtTelemetry101):
        topic = f'{self.node.alias}/{GtTelemetry101_Maker.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=json.dumps(payload.asdict()),
                            qos = QOS.AtLeastOnce.value,
                            retain=False)



One issue: some brokers restrict client_id to 23 characters. Our pattern right now is to use the node alias plus '-pub' for the publish client. We'll need to change that pattern since some of our aliases will be longer than 23 characters. But the fail is happening
with client_ids like this: "a.tank.temp3-pub" and that is only 16 characters long. Tried replacing the '-pub' with '.pub' but that did
not make a difference.