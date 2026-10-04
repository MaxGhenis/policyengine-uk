#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2; M=/tmp/uk2133r2; E=$W/.r2-evidence
cd $W
AI=policyengine_uk/tests/policy/baseline/finance/benefit/family/housing_benefit/applicable_income
for v in no_legacy old_no_legacy; do
  nohup uv run --frozen --no-sync python $E/run_yaml.py $M/$v $E/yaml_$v 1 $AI > $E/launch_$v.log 2>&1 &
done
