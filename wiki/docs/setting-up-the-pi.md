# Setting up the Pi
=======



[scada-template-1](https://drive.google.com/drive/u/0/folders/11u_83c-HHFVoydwg1Qnm-RuoNUw5vw5l) -
This is a 16 GB image that can be loaded onto any >= 16 GB microSD card. It followed this recipe:
 **Started with emonPi 16 GB SD microSD card**
power it up and use the button to cycle the screen to `enable ssh` and then hold it. Then
look at its address on the LAN (one of the screens) and ssh using username `pi` and password `emonpi2016`

Change ssh password to template password

Change hostname to scada-template

sudo nano /etc/hostname

sudo nano /etc/hosts


 **Various apt-get**
sudo apt-get update --allow-releaseinfo-change

sudo apt-get update

sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim build-essential libi2c-dev i2c-tools python-dev mosquitto-clients tmux

sudo apt clean


**Python 3.10.4**

wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz

sudo tar zxf Python-3.10.4.tgz
cd Python-3.10.4
sudo ./configure --enable-optimizations
sudo make -j 4
sudo make altinstall


echo "alias python=/usr/local/bin/python3.10" >> ~/.bashrc
source ~/.bashrc

python -V

sudo rm -rf Python-3.10.4.tgz
sudo rm -rf Python-3.10.4

**Enable interface options**

sudo raspi-config 

Navigate to Interfacing Options, select i2c, and enable it. 
Same for 1-wire

reboot

**Install repo**

Use ssh -A pi@LAN to bring my keys

In /home/pi

git clone https://github.com/thegridelectric/gw-scada-spaceheat-python.git

cd gw-scada-spaceheat-python/gw_spaceheat/

python -m venv venv

source venv/bin/activate

export TMPDIR=/home/pi/tmp

pip install -r requirements/drivers.txt

# RANDOM NOTES

When I tried the above again from scratch I was having trouble still with a claim that
there was no more memory


TODO: clean up the issues with pip. The latest `scada-template` 
regular pip was going to /usr/bin/pip and failing. Did this:
 /usr/local/bin/pip3.10 install -r requirements/drivers.txt

 sudo pip install pyModbusTCP

 resulted in this:
   WARNING: The scripts pyserial-miniterm and pyserial-ports are installed in '/home/pi/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The script dotenv is installed in '/home/pi/.local/bin' which is not on PATH.

But seems to work.

# Raspberry Pi i2c 

The first time I tried to use i2c, it was to control an [ncd_pr8-14 relay](https://docs.google.com/document/d/1DurCUDddqoAkloZs7OPQh909biuquTCC3XDcZe132yg/edit)


(See learning/by_function/ncd_pr-8-14_spst for example scripts)


After loading the various drivers, I tried to run the simple-gpio-monitor script and got this error:
 No such file or directory: '/dev/i2c-1'


[Devine Lu Linvega](https://github.com/neauoire) of [100 rabbits](http://100r.co/site/about_us.html) points out [here](https://github.com/pimoroni/inky-phat/issues/28) that the pi interface needs to be activated, first by typing 

# MQTT



testing broker access (needs to be on the same LAN as moquitto broker)
mosquitto_sub -v -u emonpi -P emonpimqtt2016 -t 'test'
mosquitto_pub -u emonpi -P emonpimqtt2016 -t 'test' -m 'hi'

mosquitto_sub -v -u emonpi -P emonpimqtt2016 -t 'emon/emonpi/power1'
mosquitto_sub -v -u emonpi -P emonpimqtt2016 -t 'emon/emonpi/vrms'

(see settings.py for username and .env for password)

# 1-wire
Followed these instructions (https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing?view=all)

sudo raspi-config, 5) Interface Options P7) 1-Wire, Select yes
sudo reboot

lsmod | grep -i w1_

look for 
w1_therm   
w1_gpio
wire

# hex code for emonpi

With the SD card that ships with the emonPi and the connected atmega, the atmega meter only reports power and voltage every 5 seconds. 

Following the directions [here](https://guide.openenergymonitor.org/technical/compiling/), I added PlatformIo to visual studio code on my mac. I updated the [src.ino](https://github.com/openenergymonitor/emonpi/blob/master/firmware/src/src.ino#L85) c code, changing 5000 to 1000 for TIME_BETWEEN_READINGS. I also changed the bool USA from false to true [here](https://github.com/openenergymonitor/emonpi/blob/master/firmware/src/src.ino#L95) and finally updated the BUILD_TAG in [platformio.ini](https://github.com/openenergymonitor/emonpi/blob/master/firmware/platformio.ini#L30) from 2.9.5 to 2.9.6 (maybe this should be more significant, like gw2.9.5??). The `firmware.hex` built on my mac in the relative directory `emonpi/firmware/.pio/build/emonpi`. 

I scp'd that over to `/opt/openenergymonitor/emonpi/firmware/compiled/latest.hex` on the Pi, and then from that same directory ran `./update`

After doing this, the emonpi meter readings did indeed start going once a second instead of every 5 seconds.

const int TIME_BETWEEN_READINGS=  1000
/opt/openenergymonitor/emonpi/firmware/compiled/update