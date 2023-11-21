# Scada as a service on the Raspberri Pi

The GridWorks spaceheat scada code can be run as serivce on the Raspberry Pi using 
[systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html) with the 
[systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html) command-line user interface. 

## Install gwspaceheat service

Install the service using the following commands:
```
sudo ln -s /home/pi/gw-scada-spaceheat-python/gwspaceheat.service /lib/systemd/system
sudo systemctl enable gwspaceheat.service
sudo systemctl start gwspaceheat.service
systemctl status gwspaceheat.service
```

View the log with:
```shell
journalctl -f -u gwspaceheat
```
