import time
import paho.mqtt.client as paho
import settings
import helpers

connected = False
broker=settings.MQTT_BROKER_ADDRESS
port = 13582
user = settings.MQTT_USER_NAME
pswd = helpers.get_secret('MQTT_PW')

def on_log(client, userdata, level, buf):
    print("log: ",buf)
    
def on_connect(client,userdata,flags,rc):
    if rc==0:
        print('client is connected')
        global connected
        connected = True
    else:
        print("connection failed")

client= paho.Client("client-0012") 
client.on_log=on_log
client.username_pw_set(user,pswd)
client.on_connect=on_connect
client.connect(broker)
client.loop_start()
a = 0
while connected != True:
    time.sleep(0.2)
while (True):
	a = a+1
	client.publish("mqtt/first","hello world !"+str(a))
client.loop_stop()
