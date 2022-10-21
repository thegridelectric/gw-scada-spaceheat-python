# GridWorks SpaceHeat SCADA

[![Tests](https://github.com/thegridelectric/gw-scada-spaceheat-python/actions/workflows/ci.yaml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/thegridelectric/gw-scada-spaceheat-python/branch/main/graph/badge.svg)][codecov]

[tests]: https://github.com/thegridelectric/gw-scada-spaceheat-python/actions/workflows/ci.yaml
[codecov]: https://app.codecov.io/gh/thegridelectric/gw-scada-spaceheat-python
========


This code is intended for running a heat pump thermal storage space heating system in a house, and doing this _transactively_. That means the heating system is capable of dynamically responding to local electric grid conditions and buying energy at the lowest cost times, while keeping the house warm. We believe this repo may be instrumental in effectively and efficiently reaching a low-carbon future. For an architectural overview of the code, and why it has something to do with a low-carbon future, please go [here](wiki/docs/architecture-overview.md).

This code is part of a larger framework. In particular it assumes there is a cloud-based actor which it refers to as the [AtomicTNode](wiki/docs/atomic-t-node.md) (short for Atomic Transactive Node) that is calling the shots on its control decisions most of the time. In addition, the code is structured in an
actor-based way, with a  collection of actors each responsible for an important but limited set
of functionality communicating to each other via messages. For a more specific description of both how these internal actors work with each other and how 
this repo fits into the larger transactive energy framework please go [here](wiki/docs/core-protocol-sequences.md); this page describes typical sequences of messages between relevant actors in the system.

 We are indebted to Efficiency Maine, who spearheaded and funded the [initial pilot](wiki/docs/maine-heat-pilot.md) using this code. As per the requirements of the initial pilot, the code is intended to:
  1) run on a raspberry Pi 4; and 
  2) to be able to use a variety of off-the-shelf actuating and sensing devices.

For information on setting up an SD card that will run this code on a Pi 4 with the correct
configuration and attached devices, please [go here](wiki/docs/setting-up-the-pi.md)
## Local Demo setup

Follow the directions below for creating a dev environment (assumes mac or Pi).

In one terminal window:

```
cd spaceheat
python run_local.py
```

WE NEED A BETTER LOCAL DEV DEMO


## Creating a Dev environment for macos or Pi


 - Use python 3.10.6
- .gitignore includes gw_spaceheat/venv for virtualenv so from gw_spaceheat directory:
  - `python -m venv venv`  
  - `source venv/bin/activate`
  - `pip install -r requirements/dev.txt`

Run the tests from the root directory of the repo with:

    pytest

A hardware layout file is necessary to run the scada locally. Find the default path the layout file with: 
    
    python -c "import config; print(config.Paths().hardware_layout)"

For initial experiments the test layout file can be used. The test layout file is located at:
    
    tests/config/hardware-layout.json

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

We use a rabbit broker with an mqtt plugin. To set this up in a dev environment:
1. Make sure you have docker installed
2. From the top level of the repo, run: `docker-compose -f dev-world-broker.yml up -d`
3. Check the broker ui at this web page: `http://0.0.0.0:15672/` username/password both `smqPublic`


## Step 2: input data and running the code
TODO:  ADD
`python run_local.py` will start up all actors meant to run on the SCADA pi. 
`python try_actors.py` gives an interactive script to selectively start some of the actors.

`python run_atn.py` will start up an `AtomicTNode` meant to run in the cloud (this will not 
remain in this repo).


