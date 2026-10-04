#!/bin/bash
set -e
W=/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2; M=/tmp/uk2133r2; E=$W/.r2-evidence
cd $W
rm -rf $M/base_fix; mkdir -p $M/base_fix
rsync -a --exclude '__pycache__' $W/policyengine_uk $M/base_fix/; cp $W/pyproject.toml $M/base_fix/
git diff --name-only 2105816c8...61da46a05 -- 'policyengine_uk/tests/policy/*.yaml' | grep -v -E "housing_benefit_universal_credit_passport.yaml|housing_benefit_on_passporting_benefit.yaml" > $E/base_fix_files.txt
while read f; do git show 2105816c8:$f > $M/base_fix/$f; done < $E/base_fix_files.txt
diff -r -q $W/policyengine_uk $M/base_fix/policyengine_uk -x __pycache__ || true
cd $M/base_fix
PYTHONPATH=$M/base_fix nohup uv run --frozen --no-sync --project $W policyengine-core test $(cat $E/base_fix_files.txt) -c policyengine_uk > $E/yaml_base_fixtures_head_code.log 2>&1 &
