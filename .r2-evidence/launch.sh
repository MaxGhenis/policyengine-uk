#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2
M=/tmp/uk2133r2
E=$W/.r2-evidence
cd $W
R=(uv run --frozen --no-sync python $E/run_yaml.py)
AI=policyengine_uk/tests/policy/baseline/finance/benefit/family/housing_benefit/applicable_income
nohup "${R[@]}" $W $E/yaml_head 6 policyengine_uk/tests/policy > $E/launch_head.log 2>&1 &
nohup "${R[@]}" $M/limb_off $E/yaml_limb_off 6 policyengine_uk/tests/policy > $E/launch_limb_off.log 2>&1 &
for v in no_min no_pence no_pence_ge old_no_min old_no_pence; do
  nohup "${R[@]}" $M/$v $E/yaml_$v 1 $AI > $E/launch_$v.log 2>&1 &
done
PT=(policyengine_uk/tests/test_housing_benefit_universal_credit_passport_properties.py policyengine_uk/tests/test_means_test_income_properties.py policyengine_uk/tests/test_council_tax_reduction_pensioner_earnings_disregard_properties.py)
nohup uv run --frozen --no-sync pytest "${PT[@]}" -q -p no:cacheprovider > $E/pytest_head.log 2>&1 &
cd $M/limb_off && PYTHONPATH=$M/limb_off nohup uv run --frozen --no-sync --project $W pytest "${PT[@]}" -q -p no:cacheprovider > $E/pytest_limb_off.log 2>&1 &
