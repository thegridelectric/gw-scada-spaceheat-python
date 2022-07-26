# GridWorks SpaceHeat SCADA

[![Tests](https://github.com/thegridelectric/gw-scada-spaceheat-python/actions/workflows/ci.yaml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/thegridelectric/gw-scada-spaceheat-python/branch/main/graph/badge.svg)][codecov]

[tests]: https://github.com/thegridelectric/gw-scada-spaceheat-python/actions/workflows/ci.yaml
[codecov]: https://app.codecov.io/gh/thegridelectric/gw-scada-spaceheat-python


## Step 1: Dev environment for macos or Pi


 - Use python 3.8.6
- .gitignore includes gw_spaceheat/venv for virtualenv so from gw_spaceheat directory:
  - `python -m venv venv`  
  - `source venv/bin/activate`
  - `pip install -r requirements/dev.txt` 

There are some scratch notes on Pi-related setup (like enabling interfaces) in docs/pi_setup.md
### Adding libraries 
- If you are going to add libraries, install pip-tools to your venv:
  - `python -m pip install pip-tools`
  - If you want to add a new library used in all contexts, then add it to requirements/base.in and run
      - `pip-compile --output-file=requirements/dev.txt requirements/dev.in`
      - ... and then make sure to re-compile all requirements.txt that reference that .in file (all of them,for base.in)


    - ... and then make sure to re-compile all requirements.txt that reference that .in file (all of them,for base.in)

We use pip-tools to organize requirements. The `.in` files clarify the key modules (including which ones are important to pin and which ones can be set to the latest release) and then the corresponding `.txt` files are generated via pip-tools. This means we always run on pinned requirements (from the .txt files) and can typically upgrade to the latest release, except for cases where the code requires a pinned older version.

The pip-tools also allow for building layers of requirements on top of each other. This allows us to have development tools that are not needed in production to show up for the first time in `dev.txt`, for example (like the pip-tool itself).

### Handling secrets and config variables
    
SETTING UP SECRETS.
Configuration variables (secret or otherwise) use dotenv module in a gitignored `.env` file, copied over from `.env-template`. These are accessed via `config.ScadaSettings`.


### Setting up MQTT
For development purposes, you can use the default values from `.env-template`.
To use a local mosquitto broker:
**Install the mosquito server**
1. `brew install mosquitto`
2. `brew services restart mosquitto`
3. if you want to the broker to start on mac startup: `ln -sfv /usr/local/opt/mosquitto/*.plist ~/Library/LaunchAgents`
4. Test using commandline pub sub.
   - In first terminal: `mosquitto_sub -t 'test'`
   - In second terminal: `mosquitto_pub -t 'test' -m 'hi'`
   - Success: the subscribing terminal outputs hi

## Step 2: input data and running the code

Input data is in the `input_data/houses.json` file. It includes house data organized by the `GNodeAlias` for the `AtomicTNode` 
representing the house. If `SCADA_WORLD_ROOT_ALIAS` in `.env` is is `w`, then the code expects the test heating system
in Jessica's garage. Otherwise it expects a _simulated_ heating system.

`python run_local.py` will start up all actors meant to run on the SCADA pi. 
`python try_actors.py` gives an interactive script to selectively start some of the actors.

`python run_atn.py` will start up an `AtomicTNode` meant to run in the cloud (this will not 
remain in this repo).

# Description of what this does

This code is intended to run on a raspberry Pi 4 attached to a number of actuating and sensing devices. It is for running a heat pump thermal storage heating system in a house, and doing this _transactively_. That means the heating system is capable of dynamically responding to local electric grid conditions and buying energy at the lowest cost times, while keeping the house warm. Most of the time, the decisions for when to charge the heating system (and how to participate in electricity markets) are made by an agent outside of the home's LAN - this agent is called the AtomicTransactive Node or AtomicTNode for short. 

The SCADA It does 5 main things:

1) It keeps track of the state of a DispatchContract that it can hold with its AtomicTNode.

2) When the DispatchContract exists and is in RemoteControl mode, it sends up sensing data to its AtomicTNode:
    a) compressed state data (mostly temperature) sent up every 5 minutes
    b) asynchronous power reporting on change
    c) debugging information etc if sensors are broken

3) When the DispatchContract exists and is active, it responds to actuating commands from the AtomicTNode. This will primarily be for the main heating elements (heat pump, boost elements) 
but can also be for other devices that can be actuated, like circulator pumps and flow valves.

4) When the DispatchContract either does not exist or it exists but is in LocalControl mode, it 
runs the heating system.

5) It keeps a pared-down version of its compressed synchronous data when it doesn't have a DispatchContract running in RemoteControl, and sends that data up when the RemoteControl begins 
again. There are different standards for how and what to keep for 1 day, 7 days and 28 days.

The code needs to be prepared for a wide range of heating system configurations and sensor/actuator
choices. The thermal store may be water-based, or a phase change material. We may or may not be able
to control the COP/output temp tradeoff in the heat pump. We may end up adding new actuating devices
as we evaluate the heating system performance.

The code will be running on a handful of houses in Maine for the winter of 2022-2023.


Please go to gw_spaceheat/README.md for application readme.

Other files and subfolders are related to code derivation using https://effortlessapi.com/ effortlessapi tools.


