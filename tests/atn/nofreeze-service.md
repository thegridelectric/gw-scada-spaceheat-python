# nofreeze as a service on the Raspberri Pi

The GridWorks nofreeze atn code can be run as serivce on the Raspberry Pi using 
[systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html) with the 
[systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html) command-line user interface. 

## Install gwspaceheat service

Install the service using the following commands:
```
sudo ln -s /home/pi/gw-scada-spaceheat-python/tests/atn/nofreeze.service /lib/systemd/system
sudo systemctl enable nofreeze.service
sudo systemctl start nofreeze.service
systemctl status nofreeze.service
```

View the log with:
```shell
journalctl -f -u nofreeze
```
