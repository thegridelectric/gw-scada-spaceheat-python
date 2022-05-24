**Step 1: Set up python environment for development**
 - Use python 3.8.6
- .gitignore includes gw_platform_django/venv for virtualenv so from gw_platform_django directory:
  - `python -m venv venv`  
  - `source venv/bin/activate`
  - `pip install -r requirements/dev.txt` 


      
- If you are going to add libraries, install pip-tools to your venv:
  - `python -m pip install pip-tools`
  - If you want to add a new library used in all contexts, then add it to requirements/base.in and run
      - `pip-compile --output-file=requirements/dev.txt requirements/dev.in`
      - ... and then make sure to re-compile all requirements.txt that reference that .in file (all of them,for base.in)

**Install the mosquito server**
1. `brew install mosquitto`
2. `brew services restart mosquitto`
3. if you want to the broker to start on mac startup: `ln -sfv /usr/local/opt/mosquitto/*.plist ~/Library/LaunchAgents`
4. Test using commandline pub sub.
   - In first terminal: `mosquitto_sub -t 'test'`
   - In second terminal: `mosquitto_pub -t 'test' -m 'hi'`
   - Success: the subscribing terminal outputs hi
