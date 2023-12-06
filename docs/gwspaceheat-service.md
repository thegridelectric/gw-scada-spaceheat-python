# Scada as a service on the Raspberri Pi

The GridWorks spaceheat scada code can be run as serivce on the Raspberry Pi using 
[systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html) with the 
[systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html) command-line user interface. 

Running the `service/install` installs the service, helper scripts, and a second service which
starts the service every 15 minutes if it is not running. This 'restart' services catches the case
where the service was manually stopped, but (accidentally) never restarted. 

Install the service with: 
```
./service/install
``` 

Check status of both services with: 
```shell
gwstatus
```

Start both services with: 
```shell
gwstart
```

Stop the main service until next 15 minute mark with: 
```shell
gwpause
```

Stop both services with: 
```shell
gwstop
```


## Install gwspaceheat services


Install the main service using the following commands:
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

Install the restart service, designed to correct manually starting and forgetting restart the service: 
```
sudo ln -s /home/pi/gw-scada-spaceheat-python/gwspaceheat-restart.service /lib/systemd/system
sudo ln -s /home/pi/gw-scada-spaceheat-python/gwspaceheat-restart.timer /lib/systemd/system
sudo systemctl enable gwspaceheat-restart.timer
sudo systemctl start gwspaceheat-restart.timer
systemctl status gwspaceheat-restart.timer
```
