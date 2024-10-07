
dev_requirements=gw_spaceheat/requirements/dev.txt

if [[ ( $@ == "--help") ||  $@ == "-h" ]]
then
  echo "Helper script to create or recreate the scada virtual env."
  echo
  echo "Run from top level of repo."
  echo
  echo "Usage: $0 [requirements file (default: $dev_requirements)]"
  echo
  exit 0
fi

rm -rf gw_spaceheat/venv
python -m venv gw_spaceheat/venv
source gw_spaceheat/venv/bin/activate
which pip
pip install --upgrade pip
pip install -r ${1:-$dev_requirements}
