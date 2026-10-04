#!/bin/bash
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2; E=$W/.r2-evidence
cd $W
for i in 0 1 2 3; do
  ONLY=$E/mask_retry_cases.json nohup uv run --frozen --no-sync python $E/masking_detector.py $i 4 $E/mask_retry_$i.json > $E/mask_retry_$i.log 2>&1 &
done
