#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2
E=$W/.r2-evidence
cd $W
for i in 0 1 2 3 4 5; do
  nohup uv run --frozen --no-sync python $E/masking_detector.py $i 6 $E/mask_head_$i.json > $E/mask_head_$i.log 2>&1 &
done
# Positive control: the 407acbd80 fixtures (with 407acbd80 code) for the files the round-1 review and author touched
O=/tmp/uk2133r2/old_clean
for f in housing_benefit_applicable_income_disregard housing_benefit_eligible lifetime_isa_capital housing_benefit_applicable_income.yaml; do
  (cd $O && FILTER=$f PYTHONPATH=$O nohup uv run --frozen --no-sync --project $W python $E/masking_detector.py 0 1 $E/mask_old_$f.json > $E/mask_old_$f.log 2>&1 &)
done
