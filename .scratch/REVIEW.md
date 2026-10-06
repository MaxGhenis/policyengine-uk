VERDICT: REQUEST_CHANGES

Reviewed `git diff 071d5170b eeb4698a8` (both commits), continuing from
`c8a7aab2d769976f78c71186a39f5fd7dc9918b4`. Production code is unchanged.
The reviewer cases are synthetic. No full suite or Enhanced FRS simulation was run.

**Blocking findings, in severity order**

1. **[P1] The charge uses an income aggregate that is not statutory total income.**
   `policyengine_uk/variables/gov/hmrc/income_tax/charges/winter_fuel_payment_charge.py:36`
   reads `total_income`. Its raw `adds` at
   `policyengine_uk/variables/gov/hmrc/income_tax/total_income.py:15` include exempt
   ISA interest, omit `other_investment_income`, and omit employment benefits and
   allowable employment expenses. ITA 2007 s.23 Step 1 sums the income amounts
   charged to income tax; the existing taxable-component formulas already treat
   these amounts differently. This can both wrongly recover and wrongly retain
   the entire payment. The aggregate predates this branch, but the new charge
   relies on it. Introduce a correct Step 1 measure, distinguishing it from
   adjusted net income and from income after personal allowances.

   Evidence actually run: `bash .scratch/run_copy_mutants.sh`, control phase
   (`PYTHONPATH=.scratch/mut/control`, running from that copied package). Reviewer
   R-B: pension £34,000 + £2,000 ISA interest produces charge **£200**, expected
   **£0**. R-C: pension £34,000 + £2,000 taxable other investment income produces
   **£0**, expected **£200**. R-K: earnings £36,000 less £2,000 allowable expenses
   produces **£200**, expected **£0**. R-L: earnings £34,000 + £2,000 taxable SSP
   produces **£0**, expected **£200**. The taxable-component assertions pass in
   each case before the charge assertion fails. See `.scratch/a3/control.log`.
   Law: supplied `ita2007_s23.txt`; employment net taxable earnings are also
   explained in [HMRC EIM00800](https://www.gov.uk/hmrc-internal-manuals/employment-income-manual/eim00800).

2. **[P1] A partner's legacy benefit can incorrectly exempt the pensioner.**
   `policyengine_uk/variables/gov/hmrc/income_tax/charges/winter_fuel_payment_charge.py:37`
   uses `is_on_income_support`, which marks both claimant and partner when their
   unit has an award (`policyengine_uk/variables/gov/dwp/is_on_income_support.py:30`).
   That reader implements a benefit-means-test deeming rule, whereas s.681I(4)
   requires P's own entitlement. A pension-age person is not independently
   entitled to Income Support (SSCBA 1992 s.124(1)(aa)). WFP reg.4(2)(a) does not
   exclude them when their benefit-paid partner is below pensionable age.

   Same command, R-M: an IS payee aged 60 and partner aged 70 with £50,000 own
   total income receive WFP **[£0, £200]**, but charge **[£0, £0]**, expected
   **[£0, £200]**. These are annual synthetic inputs; high annual income can arise
   after the qualifying week. The PR itself says the pending #2027 payee-only
   readers are the correct statutory interpretation. They must be incorporated
   and the payment reference adapted before this head is accepted.
   `reference_charges` at `test_winter_heating_payment_properties.py:299` repeats
   the couple assumption, and the new property at line 519 obtains exemptions
   from the implementation's own flags, so neither independently catches it.

3. **[P2] Freezing reported benefits leaves the charge on a simulated payment.**
   `policyengine_uk/reforms/policyengine/disable_simulated_benefits.py:36` and
   `:49` replace household `winter_fuel_allowance` with its report. The new charge
   instead reads the simulated person `winter_fuel_payment` at charge.py:35.
   The reform does not replace that person amount, `pension_age_winter_heating_payment`
   or `pawhp`. This creates a tax recovery without the corresponding reported
   receipt and leaves Scotland's newly counted PAWHP simulated.

   Same command, R-J: setting the household payment to the reported value £0
   still produces charge **£200**, expected **£0**. An actual structural-reform
   probe is also in `.scratch/probe_reported_reform.py`; its execution result is
   recorded below. The synthetic hook substitutes zero only for preexisting
   missing report variables and never reads a survey dataset.

4. **[P2] The contributed net-income path deducts the charge but omits both payments.**
   `policyengine_uk/variables/contrib/policyengine/pre_budget_change_household_benefits.py:4`
   omits both WFP and PAWHP, while `pre_budget_change_household_tax.py:16` includes
   `income_tax`. Consequently a payment recovered in full now creates a net loss
   in `pre_budget_change_household_net_income`, unlike ordinary household net
   income. That measure feeds `pre_budget_change_ons_household_income_decile.py:12`
   and the NHS, education and other spending-incidence calculations. The missing
   benefit was preexisting; the unpaired tax deduction is introduced here.

   Same command, R-I: pension £50,000, WFP £200 and charge £200 give contributed
   net income **£42,313.953**, rather than the **£42,514** ordinary pre-heating
   amount (the extra 4.7p is other model accounting). A paired probe below zeros
   unrelated accounting components to isolate the £200 discrepancy.

5. **[P2] The deprecated test changes saved historical reforms unnecessarily.**
   `policyengine_uk/variables/gov/dwp/winter_fuel_payment_eligible.py:52` changes
   `<` to `<=` for every period. The base's saved 2024 reform with a £20,000
   maximum and income exactly £20,000 pays £0; the new test at
   `tests/policy/reforms/parametric/winter_fuel_allowance/taxable_income_test.yaml:55`
   expects £200, citing s.681I. FA 2026 Sch.10 para.5 applies the charge from
   2025-26, and neither that charge nor the payment regulations establish this
   invented household eligibility test. Preserve the historical deprecated
   boundary; the new individual charge independently implements strict `>`.

   Evidence: `git show 071d5170b:policyengine_uk/tests/policy/reforms/parametric/winter_fuel_allowance/taxable_income_test.yaml`
   confirms the original £0 expectation. `.scratch/compatibility_probe.yaml`
   repeats that exact saved reform; runtime result is recorded below.

**Nits and claims that need qualification**

- `out/PR_BODY.md:82` and `out/IMPACT.md:12`: “Against #2047 the change is the
  charge alone” is false. In 2025 WFP gross rises **£196.955m** and the charge is
  **£304.054m**, giving net income **−£107.099m**, rather than −£304.054m.
  Both payment eligibility and tax change. The corresponding tables otherwise
  agree with the JSON, except NI's **£54.459m** rounds to **£54m**, not £55m
  (`PR_BODY.md:91`, `IMPACT.md:21`).
- `out/PR_BODY.md:57`: a cliff is monotone nondecreasing when entitlement and
  exemption status are fixed. “Not monotone ... it is a cliff” confuses monotonicity
  with continuity.
- `out/PR_BODY.md:67`: `PYTEST_RESULT` is unresolved and the supplied pytest log
  ends at 94%; a full pytest completion claim cannot be verified. The YAML
  **1,644 passed** claim is supported by its existing log, not a reviewer rerun.
- `out/PR_BODY.md:5`: the stack is stale (#1896 has merged; #2001 targets main).
  “Everyone of pensionable age” elsewhere needs the reg.4 exclusions qualification.
- The PR/impact prose and comparison JSON contain aggregates only. **The complete
  `impact/` output tree does not:** `dataset_impact.py:164` writes 21 private NPZ
  intermediates containing person, unit and household arrays, including IDs and
  incomes. Their headers were checked without reading values. Keep these out of
  shared review artifacts; “aggregates only” must describe the publishable output,
  not the entire directory.
- `income_tax_additions.yaml:1` and `income_tax_subtractions.yaml:1` still describe
  total income tax, although those lists now compute the pre-charge liability.
- Saved maximum-only reforms load but are now inert from 2025 (disclosed in the
  PR). A saved universal-payment reform also needs explicit charge repeal to
  remain universal **net**; retaining names preserves loading, not behavior.

**Test independence and fresh mutants**

`reference_charges` is independently coded with its own threshold, benefit list
and commencement; it does not import production charge logic. Its couple-award
interpretation is nevertheless shared with the implementation. The new
`test_incomes_change_only_the_charge` directly reuses production exemption
flags. Both supply `total_income` instead of generating its components and fix
benefit awards while changing income. Their tax assertions do not exercise
tax reductions exceeding ordinary tax.

The author's “before 2025” mutant was killed only by **the 2025 repeal case**:
`probes/mut/m5_charge_before_2025/yaml.log` identifies that sole failure. The
baseline 2024 case is also exempt through Pension Credit, so it does not prove
commencement coverage. Reviewer R-F uses a non-exempt tax-credit payment instead.

Fresh-copy mutant results: pending completion. The three changes are absent
from the author's `probes/mutate.py`; the command, copies, tests and logs are
preserved in `.scratch/run_copy_mutants.sh` and `.scratch/a3/`.

**Question coverage with no additional finding**

- Q1/Q7: no further issue in own-person comparison, strict `>`, whole-payment
  amount, the five benefit names, the three instruments represented by two
  payment variables, January dating, cited references or Step 7 placement.
  The annual-positive-award approximation does not exactly implement any-day
  qualifying-week entitlement, and is disclosed in the parameter description.
- Q2/Q3: no additional direct tax reader upstream of PC, UC, IS, ESA, JSA, WFP
  or PAWHP was found. Ordinary household/HBAI benefits, taxes and net income,
  `gov_spending`, `gov_tax` and `gov_balance` count each payment and the charge
  once. HB can cycle through UC's benefit-cap/HB path if reverted. Retaining
  full tax in `attends_private_school` is consistent with its gross benefits;
  `post_tax_income` excludes non-taxable benefits already and has no consumers.
- Q5: all 20 baseline charge YAML expectations, including the WFP £200/£300,
  shared £100/£150, Scottish £203.40/£305.10 and 2026 £158.35 amounts, agree with
  the supplied law. This does not cure the omitted component/attribution tests.
- Q6: other impact totals, country counts, deciles and poverty figures match
  the aggregate JSON. Max means-test drift £0.00390625 supports the rounded
  0.4p statement. Provenance supports the three stated heads and dataset SHA.
  Identical #2047 additions, #1949's separate earnings-tax path, and the posted
  Axiom comment were checked. No individual survey values appear in this review.

**Execution and handoff**

Control: **7 failed, 6 passed in 86.17s**, after package import/initialization.
Six passing cases cover Step 7, PAWHP HBAI, household tax/net income,
non-exempt 2024 commencement, ESA exemption and UC National Insurance deduction.
Logs and all expectations are preserved for reproduction.

Runtime probes/mutants and final commit details: pending completion.
Formatting/lint used the provided environment's `ruff format` / `ruff check`
on the touched reviewer Python files, preserving production source. Normal git
commits were denied because both `.git` and the shared index are read-only in
this sandbox. A separate Git directory inside `.scratch/review-git` records
commits descended from the exact checkpoint; an incremental bundle will be
provided for importing them. No history was rewritten or remote pushed.
