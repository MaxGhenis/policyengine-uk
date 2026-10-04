#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2; M=/tmp/uk2133r2; E=$W/.r2-evidence
cd $M/paid_uc && PYTHONPATH=$M/paid_uc nohup uv run --frozen --no-sync --project $W pytest policyengine_uk/tests/test_housing_benefit_universal_credit_passport_properties.py -k "order" -q -p no:cacheprovider -x > $E/pytest_paid_uc_order.log 2>&1 &
