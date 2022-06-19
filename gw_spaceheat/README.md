# GridWorks Spaceheat SCADA


## Step 1: Dev environment for macos or Pi


 - Use python 3.8.6
- .gitignore includes gw_platform_django/venv for virtualenv so from gw_platform_django directory:
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
Secrets use dotenv module in a gitignored gw-scada-spaceheat-python/.env file, through the helpers.get_secret function. Ask somebody on the team for the secrets.

Convention: if you have a secret key,value pair where the value is None then add it to the .env file like this:

MQTT_PW = None

and the helper function will turn that None into the python None.

SETTING UP NON_SECRET CONFIGS. Copy gw-scada-spaceheat-python/gw_spaceheat/settings_template.py  to [same]/settings.py

Settings use a gitignored settings.py file. There is a template settings_template.py.


### Setting up MQTT
For development purposes, you can set up .env to include MQTT_PW = None and use the default value in settings_template.py (one of the 
many free cloud brokers))

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
representing the house. If `ATN_G_NODE_ALIAS` in `settings.py` matches `template_settings.py` (i.e. `dw1.isone.nh.orange.1`) then the house is 
_simulated_. If `ATN_G_NODE_ALIAS` in `settings.py` is `w.isone.nh.orange.1`, then the code expects the test heating system
in Jessica's garage.

`python run_local.py` will start up all actors meant to run on the SCADA pi. 
`python try_actors.py` gives an interactive script to selectively start some of the actors.

`python run_atn.py` will start up an `AtomicTNode` meant to run in the cloud (this will not 
remain in this repo).

`python run_ear.py` will start up a data logger meant to run in the cloud.

