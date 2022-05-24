## Step 1: Set up python environment for development
 - Use python 3.8.6
- .gitignore includes gw_platform_django/venv for virtualenv so from gw_platform_django directory:
  - `python -m venv venv`  
  - `source venv/bin/activate`
  - `pip install -r requirements/dev.txt` 


### Adding libraries 
- If you are going to add libraries, install pip-tools to your venv:
  - `python -m pip install pip-tools`
  - If you want to add a new library used in all contexts, then add it to requirements/base.in and run
      - `pip-compile --output-file=requirements/dev.txt requirements/dev.in`
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

## Step 2: input data and running the code

Input data is in input_data folder. The `dev_house.json` is used for developing on a mac. The `pi_dev_house.json` is used for a pi that is connected to actual hardware and has its various drivers (like i2c) enabled.

Run the code in main.py as a script. It creates the main code for the primary scada actor, loading its input data by checking if the OS belongs to a mac or not.