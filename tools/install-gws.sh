if [[ ( $@ == "--help") ||  $@ == "-h" ]]
then
  echo "Helper script to add the 'gws' cli to the path."
  echo
  echo "Run from top level of repo."
  echo
  echo "Usage: $0"
  echo
  exit 0
fi

rm gw_spaceheat/venv/bin/gws > /dev/null 2>&1
ln -s `pwd`/gw_spaceheat/gws gw_spaceheat/venv/bin
