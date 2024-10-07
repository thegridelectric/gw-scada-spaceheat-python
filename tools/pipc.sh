# Helper script to update requirements .txt files from .in files
#
# Run from top level of repo.
if [[ ( $@ == "--help") ||  $@ == "-h" ]]
then
  echo "Helper script to create or recreate the scada virtual env."
  echo
  echo "Run from top level of repo."
  echo
	echo "Usage: $0 [requirements file (default: 'gw_spaceheat/requirements/')]"
	exit 0
fi

pip-compile gw_spaceheat/requirements/base.in -o gw_spaceheat/requirements/base.txt --upgrade-package gridworks-protocol
pip-compile gw_spaceheat/requirements/drivers.in -o gw_spaceheat/requirements/drivers.txt --upgrade-package gridworks-protocol
pip-compile gw_spaceheat/requirements/test.in -o gw_spaceheat/requirements/test.txt --upgrade-package gridworks-protocol
pip-compile gw_spaceheat/requirements/dev.in -o gw_spaceheat/requirements/dev.txt --upgrade-package gridworks-protocol
git status
git diff | grep gridworks
