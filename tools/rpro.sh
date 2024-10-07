dev_requirements=gw_spaceheat/requirements/dev.txt

if [[ ( $@ == "--help") ||  $@ == "-h" ]]
then
  echo "Helper script which restore virtual env to using gwproto and gwproactor as defined in requirements file."
  echo
  echo "Run from top level of repo."
  echo
	echo "Usage: $0 [requirements file (default: $dev_requirements)]"
	exit 0
fi

pip uninstall gridworks-proactor
pip uninstall gridworks-protocol
pip install -r ${1:-$dev_requirements}
python -c "import gwproto; import gwproactor; print(gwproto.__file__); print(gwproactor.__file__)"