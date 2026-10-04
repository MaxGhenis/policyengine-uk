#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2; M=/tmp/uk2133r2; E=$W/.r2-evidence
FILES=($(cat $E/mask_python_files.txt))
[ ${#FILES[@]} -eq 28 ] || { echo "bad file list"; exit 1; }
run() { # name root
  local name=$1 root=$2
  (cd $root && PYTHONPATH=$root nohup uv run --frozen --no-sync --project $W pytest "${FILES[@]}" -n 4 -q -p no:cacheprovider --junitxml=$E/pymask_$name.xml > $E/pymask_$name.log 2>&1 &)
}
run head $W
run limb_off $M/limb_off
run pert_on $M/pert_on
run pert_off $M/pert_off
