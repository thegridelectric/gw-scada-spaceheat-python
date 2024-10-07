if [[ ( $@ == "--help") ||  $@ == "-h" ]]
then
  echo "Helper script which updates virtual env to use local copy of gwproto and gwproactor"
  echo
  echo "Run from top level of repo."
  echo
  echo "Usage: $0"
  echo
  exit 0
fi

deactivate | true
source gw_spaceheat/venv/bin/activate
pip uninstall gridworks-protocol
pip uninstall gridworks-proactor
pip install -e ../gridworks-proactor --no-cache-dir
pip uninstall gridworks-protocol
pip install -e ../gridworks-protocol
python -c "import gwproto; import gwproactor; print(gwproto.__file__); print(gwproactor.__file__)"
