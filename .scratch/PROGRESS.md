# Review journal (attempt a2)
- a1 left: control run of 178 targeted YAML tests = all pass (174s); mutate_review.py with r1..r9 mutants; no findings recorded.
- a2: reading diff, law, tests, claims.
## a2 findings so far (to verify by running)
- total_income = raw adds (employment_income, private_pension_income, social_security_income, self_employment_income, property_income, savings_interest_income, dividend_income, miscellaneous_income). Step 1 components (model's taxable_* = adjusted_net_income_components) differ: ISA interest excluded, other_investment_income included, SSP/SMP included, employment expenses / trading / property / capital allowances deducted. -> law finding (total income overstated/understated).
- Step 7 placement correct in code, but no test exercises Step 6 reductions > Step 5 tax (r1 mutant likely survives).
- HB/CTR switches: not needed for circularity (check r2/r3 no CycleError); changelog says circular.
- disable_simulated_benefits reform: overrides winter_fuel_allowance (household) with reported, but charge reads person winter_fuel_payment; pawhp not in list.
- pre_budget_change_household_tax includes income_tax (charge) but pre_budget_change_household_benefits has no WFA/pawhp.
- post_tax_income (household) = total_income - income_tax - NI: now nets charge with no payment (no readers).
- PR_BODY has unfilled 'pytest: PYTEST_RESULT' placeholder.
- Saved reforms setting require_benefits false (universal WFP) now keep the charge: undocumented.
- 2024 baseline YAML 'no charge before 2025-26' is vacuous (pensioner on PC -> exempt anyway).
- Hypothesis: reference_charges restates the couple-award reading; test_incomes_change_only_the_charge reads model is_on_* (not independent); total_income input directly so income definition untested; pre-charge tax 0 so Step 7 assertion trivially true.
## a2 evidence (13:10)
- reviewer_tests.yaml v1 on branch (separate process, policyengine-core test, 569s): R-A Step7 PASS, R-F 2024 TC PASS, R-B ISA FAIL (charge 200 vs 0), R-C other_investment FAIL (0 vs 200), R-D/R-E FAIL due to my own expectations (PC simulated; TV licence 174.50). Fixed to v2 before in-process control collected. Log: reviewer_tests_branch_v1.log.
- EFRS h5 (aggregates only): no ISA / other_investment_income / other_tax_credits / employment_expenses columns; 66+: 12.00m people; savings interest 7.25m people £25.4bn; property income 0.75m £20.6bn; 15k with property income in (0,1000]; employee pension contribs 0.26m £0.27bn.
- Claims verified: #2047 adds identical 3 lines, merge-tree clean with eeb4698a8; #1949 uc_income_tax_on_earnings does not read income_tax; impact tables match branch_vs_base*.md; means-test list in compare_impact.py covers PC/UC/IS/ESA/JSA/HB/CTB/TC/benefit cap; PR stack: #2001 now -> main, #1896 MERGED (stale chain text); pytest_full.log stops at 94%, PYTEST_RESULT placeholder unfilled.
- In-process mutant runner: .scratch/run_mutants_inproc.py -> .scratch/inproc/summary.txt (started ~13:00).
