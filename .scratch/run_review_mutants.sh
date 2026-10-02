#!/bin/bash
# Run the reviewer's mutants (mutate_review.py) one at a time against the
# targeted YAML tests. PYTHONPATH points at the mutant copy, which wins over
# the caller's editable install. Usage: run_review_mutants.sh <mutant>...
cd "$(dirname "$0")"
SRC=$(cd .. && pwd)
VENV=$HOME/PolicyEngine/_worktrees/pe-uk-winter-fuel-payment-charge/.venv/bin
T=policyengine_uk/tests/policy
TESTS="
$T/baseline/gov/hmrc/income_tax/charges/winter_fuel_payment_charge.yaml
$T/baseline/gov/dwp/winter_fuel_payment/relevant_benefit_receipt.yaml
$T/baseline/gov/social_security_scotland/pawhp.yaml
$T/reforms/parametric/winter_fuel_allowance
$T/reforms/parametric/winter_fuel_payment_charge
$T/baseline/finance/benefit/family/housing_benefit/applicable_income/housing_benefit_applicable_income.yaml
$T/baseline/finance/benefit/family/income_support/legacy_family_definitions.yaml
$T/baseline/finance/benefit/family/universal_credit/income/uc_earned_income.yaml
$T/baseline/gov/dwp/pension_credit/claimant_partner_income_and_carers.yaml
$T/baseline/gov/dwp/benefit_cap.yaml
$T/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml
$T/baseline/gov/dwp/means_test_income_members.yaml
$T/baseline/finance/benefit/family/legacy_award_readers/means_test_income.yaml
"
for m in "$@"; do
  $VENV/python mutate_review.py "$SRC" "$m" > /dev/null || { echo "$m: MUTATE FAILED"; continue; }
  d=mut/$m
  (cd $d && PYTHONPATH=$PWD $VENV/python -c "import policyengine_uk; print(policyengine_uk.__file__)" > which.log 2>&1)
  (cd $d && PYTHONPATH=$PWD $VENV/policyengine-core test $TESTS -c policyengine_uk > yaml.log 2>&1)
  y=$(grep -Eo '[0-9]+ (failed|passed)[^=]*' $d/yaml.log | tail -1)
  echo "$m [$(cat $d/which.log)] yaml: $y"
  grep -E "^FAILED" $d/yaml.log | head -8
done
