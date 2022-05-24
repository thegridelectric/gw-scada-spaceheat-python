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

We use pip-tools to organize requirements. The `.in` files clarify the key modules (including which ones are important to pin and which ones can be set to the latest release) and then the corresponding `.txt` files are generated via pip-tools. This means we always run on pinned requirements (from the .txt files) and can typically upgrade to the latest release, except for cases where the code requires a pinned older version.

The pip-tools also allow for building layers of requirements on top of each other. This allows us to have development tools that are not needed in production to show up for the first time in `dev.txt`, for example (like the pip-tool itself).