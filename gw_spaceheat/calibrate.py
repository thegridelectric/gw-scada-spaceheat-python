import os
import subprocess
import time



def kill_sensors():
    output = os.popen('ps -A  | grep try_multiple_temp_sensors').read()
    possibles = str(output).split('\n')
    for line in possibles:
        if 'try_multiple_temp_sensors.py' in line:
            pid = line.split(' ')[0]
            os.system(f'kill -9 {pid}')
            print(f'Killed try_multiple_temp_sensors process {pid}')

kill_sensors()


while True:
    cmd = ['python', 'try_multiple_temp_sensors.py']
    sensor_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    print("sensors restarted")
    time.sleep(30)
    kill_sensors()
    print("sensors killed)")
    time.sleep(10)
