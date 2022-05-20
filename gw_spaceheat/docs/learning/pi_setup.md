The scada pi was choking on sudo apt-get update 
(This must be accepted explicitly before updates for this repository can be applied. See apt-secure(8) manpage for details)

This worked:
sudo apt-get update --allow-releaseinfo-change

# python 3.8.6

followed these instructions:
https://installvirtual.com/how-to-install-python-3-8-on-raspberry-pi-raspbian/


sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev 
libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev 
libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim

wget https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz

sudo tar zxf Python-3.8.6.tgz
cd Python-3.8.6
sudo ./configure --enable-optimizations
sudo make -j 4
sudo make altinstall


echo "alias python=/usr/local/bin/python3.8" >> ~/.bashrc
source ~/.bashrc

python -V

sudo rm -rf Python-3.8.6.tgz
sudo rm -rf Python-3.8.6


ADDING smbus-cffi

DIRECTIONS FROM  https://pypi.org/project/smbus-cffi/

sudo apt-get install build-essential libi2c-dev i2c-tools python-dev libffi-dev


regular pip was going to /usr/bin/pip and failing. Did this:
 /usr/local/bin/pip3.8 install -r requirements/drivers.txt


# Raspberry Pi i2c 

The first time I tried to use i2c, it was to control an [ncd_pr8-14 relay](https://docs.google.com/document/d/1DurCUDddqoAkloZs7OPQh909biuquTCC3XDcZe132yg/edit)


(See learning/by_function/ncd_pr-8-14_spst for example scripts)


After loading the various drivers, I tried to run the simple-gpio-monitor script and got this error:
 No such file or directory: '/dev/i2c-1'


[Devine Lu Linvega](https://github.com/neauoire) of [100 rabbits](http://100r.co/site/about_us.html) points out [here](https://github.com/pimoroni/inky-phat/issues/28) that the pi interface needs to be activated, first by typing sudo raspi-config and then
navigating to Interfacing Options, selecting i2c, and enabling it.

