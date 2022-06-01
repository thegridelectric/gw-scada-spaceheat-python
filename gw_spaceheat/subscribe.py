import time
import paho.mqtt.client as mqtt
import settings
import helpers

def on_connect(client,userdata,flags,rc):
    if rc==0:
        print('client is connected')
        global connected
        connected = True
    else:
        print("connection failed")

def on_message(client,userdata,message):
    print("Message received : "+str(message.payload.decode("utf-8")))
    print("Topic : "+str(message.topic))

def on_log(client, userdata, level, buf):
    print("log: ",buf)

connected = False
Messagereceived = False

broker=settings.MQTT_BROKER_ADDRESS
user = settings.MQTT_USER_NAME
pswd = helpers.get_secret('MQTT_PW')

client= mqtt.Client("client-00123")
client.on_message=on_message
client.on_log=on_log
client.username_pw_set(user,pswd)
client.on_connect=on_connect
client.connect(broker)
client.loop_start()
client.subscribe("mqtt/first")

while connected != True:
    time.sleep(0.2)

while Messagereceived != True:
    time.sleep(0.2)

client.loop_stop()
