#Debug mosquitto

To see the issue on a mac:

I did the out-of-the box `brew install mosquitto` to get a mosquitto mqtt broker on my mac.

`python main.py` to start up the primary scada, which is listening for temp readings

`python try_temp_sensor.py` to run the simulated temp sensor publishing data about every 880 ms

The priary scada gets the messages for some period of time, but usually in under a minute it stops receiving tem. Killing and restarting `try_temp_sensor.py` and the scada starts getting them again.

So it looks like the sensor _thinks_ it is publishing its messages to the topic, but it is not.


The primary mqtt in the code is in `actors/actor_base.py`. The publishing happens in `actors/sensor_base.py` with these lines:

def publish_gt_telemetry_1_0_1(self, payload: GtTelemetry101):
        topic = f'{self.node.alias}/{GtTelemetry101_Maker.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=json.dumps(payload.asdict()),
                            qos = QOS.AtLeastOnce.value,
                            retain=False)
        self.screen_print(f"Just published {payload} to topic {topic}")
