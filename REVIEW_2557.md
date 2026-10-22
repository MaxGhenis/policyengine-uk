VERDICT: REQUEST_CHANGES
Head reviewed: d8aae1b12

# Review of PolicyEngine/policyengine-uk#2557 (benefit uprating by September CPI)

Full review of head `d8aae1b129ad8f1b475a88cd75b54258bf32389e` (one commit on `582b86315`). Reviewer: UK hub independent review (Opus 5.5, Subfleet job `20261022-010709-uk2557-review-w`). Nothing was pushed or posted.

The core change is right. Section 150 benefits rise each April by the previous September's CPI. September 2026 CPI is 3.5% (checked against ONS). The new index reproduces every published September rise from April 2011 to April 2027, and the UC Act 2025 indices now read September CPI as ss1(3) and 4(4) require. The triple lock is unaffected (earnings 3.9% binds). The aggregate-impact directions are all as expected.

Two things block the merge:
- **B1:** CI is red on the PR's own head.
- **B2:** One amount that names the index (the UC childcare cap) still doesn't move, and the PR's "every parameter on the index" test can't see it.

Both are small fixes. There are also four should-fix items (S1–S4) and four follow-ups (F1–F4).

## Blocking

### B1. CI fails: a DfE test still expects the benefit index
`policyengine_uk/tests/test_childcare_funding_rates.py:161` pins `gov.dfe.childcare_funding_rate` to `gov.benefit_uprating_cpi`. This PR repoints those rates to `indices.obr.lagged_cpi` (`policyengine_uk/parameters/gov/dfe/childcare_funding_rate.yaml:14`).

CI `Test / Python 1/5` (job 119648992238) fails with 1 failed, 1565 passed:
- Failing test: `test_existing_cpi_projection_starts_from_the_2026_funding_anchor`.
- Actual: `[12.3169, 9.1047, 6.7620]`. These are 2026 × 1.023, the lagged calendar CPI the PR intends.
- Expected: `[12.4614, 9.2115, 6.8413]`. These are 2026 × 1.035.

The test file is unchanged since the base (`git log` shows only e8e2cd39e). So the PR head itself breaks it; this is not an interaction with newer main. The PR body says the targeted pytest covered "every file that reads `cpi_september` or the benefit index". This file reads the benefit index and wasn't run.

**Fix:** compute `factor` from `gov.economic_assumptions.indices.obr.lagged_cpi` (2027 over 2026), matching the retained projection.

### B2. UC childcare costs cap never uprates, and the invariant test misses it
`policyengine_uk/parameters/gov/dwp/universal_credit/elements/childcare/cap.yaml:17` declares `uprating: gov.benefit_uprating_cpi` on the node, without `propagate_metadata_to_children`. policyengine-core's `uprate_parameters` reads `uprating` only from leaf `Parameter` metadata. So `cap.1` and `cap.2` carry no uprating and stay at £1,071.09 and £1,836.16 a month for good (checked: identical 2026 to 2041).

The cap is live: `uc_maximum_childcare_element_amount.py:14` reads `p.cap[...]`. In practice it is a September CPI amount: +6.7% in 2024, +1.7% in 2025 and +3.8% in 2026, from the file's own values.

`test_every_parameter_on_the_index_rises_by_september_cpi_after_its_last_value` (`policyengine_uk/tests/test_september_cpi_uprating.py:126-128`) collects only leaves whose own metadata names the index, so it skips these two silently.

This is older than this PR (main freezes the cap too). But it falls inside the PR's stated invariant, and the fix is one line.

**Fix:** add `propagate_metadata_to_children: true` to `cap.yaml` metadata. Verified on a scratch export of the head: the caps become £1,108.58 and £1,900.42 for April 2027 (× 1.035). Then make the test fail on a node-level `uprating` that doesn't reach its leaves. For example, assert that no `ParameterNode` has `uprating` metadata while any of its leaves lack it. A scan of the head finds this is the only such node, apart from `household.wealth.national_balance_sheet.household`.

## Should fix in this PR (not blocking)

### S1. HB non-dependant deduction income bands are earnings-linked but now move by September CPI, unflagged
`policyengine_uk/parameters/gov/dwp/housing_benefit/non_dep_deduction/amount.yaml:120-123` propagates `gov.benefit_uprating_cpi` to both each bracket's `amount` and its `threshold`.

The deduction amounts follow September CPI (2021–2026, all within 5p). The income bands follow May–July earnings, rounded to £1. Taking the file's values, band 2 went 139 → 143 → 149 → 149 → 154 → 162 → 176 → 183 → 192:

| April | Band rise | AWE (May–July before) | September CPI |
|---|---:|---:|---:|
| 2019 | 2.5–2.9% | 2.6% | 2.4% |
| 2020 | 3.8–4.2% | 3.9% | 1.7% |
| 2021 | 0% (SI 2021/162 art 24(3), cited in the file) | −1.0% | 0.5% |
| 2023 | 5.2–5.6% | 5.5% | 10.1% |
| 2024 | 8.4–8.6% | 8.5% | 6.7% |
| 2025 | 3.9–4.2% | 4.1% | 1.7% |
| 2026 | 4.75–4.9% | 4.8% | 3.8% |

In 2022, when the earnings element was suspended, they rose about 3.2–3.4%. The earnings column is the model's own `awe_total_pay_may_july`.

By the PR's own rule (amounts the review doesn't raise by September CPI keep their previous projection), these belong with the SMG group. Numerically the change is not a regression for April 2027: base 2.3%, PR 3.5%, likely actual about 3.9%. But they should at least carry a comment saying they are earnings-linked and appear in the README and changelog list and the follow-up. Better: give each `threshold` its own `uprating` (lagged CPI, or an earnings index when the SMG follow-up adds one).

### S2. "Outside the s150 prices review" is legally wrong for two of the five amounts
`policyengine_uk/parameters/gov/economic_assumptions/README.md:198-202`, `changelog.d/benefit-uprating-september-cpi.changed.md:1` and the commit message group the SMG, savings credit threshold, HB pension-age allowances, DfE rates and council tax surcharge as "amounts outside the s150 prices review". Two of them are inside it:
- **Savings credit threshold:** SSAA 1992 s150(1)(l) covers sums in regulations under ss2 or 3 of the State Pension Credit Act 2002, excluding only the s150A(1)(d) SMG. So the threshold (SPCA s3) is inside the s150 review.
- **HB pension-age allowances:** s150(1)(h) covers sums "specified in regulations under section 135(1)" SSCBA (HB applicable amounts), so these are inside too.

Both are reviewed under s150 and raised at discretion under s150(2)(b) by more than prices. HCWS1101 (26 Nov 2025) states that the savings credit *maximum* rose 3.8% with CPI. The threshold follows from that and the SMG. With maximum = 60% × (SMG − threshold), the model's own values give a 2026 maximum of (£238.00 − £208.08) × 60% = £17.95, which is £17.30 × 1.038. The threshold then rises 4.9% because the SMG rose 4.8% on earnings.

Only the SMG (s150A), DfE rates and the surcharge are outside s150.

**Fix:** say "not raised by September CPI in practice" (as the per-file YAML comments already correctly do) rather than "outside the s150 prices review".

### S3. Stale docstring
`policyengine_uk/tests/test_september_cpi_uprating.py:139` says "0% in April 2016, 2.1% in April 2027". With September 2026 published, April 2027 is 3.5%; 2.1% is April 2028.

### S4. May–July 2026 earnings is no longer provisional
ONS KAC3 in the 20 October 2026 labour market release still gives 3.9% for May–July 2026: the API's `releaseDate` is 2026-10-19T23:00Z and the "2026 JUL" three-month figure is 3.9. Two places still call it provisional or a first estimate:
- `policyengine_uk/parameters/gov/economic_assumptions/statutory_uprating_inputs/awe_total_pay_may_july.yaml:29-31` ("Provisional ... replace it once published").
- The docstring at `policyengine_uk/tests/test_triple_lock_statutory_inputs.py:55` ("first estimate").

The value needs no change; only the wording. This can also be left to the triple-lock project's input job if that is where the hub wants it.

## Follow-ups (older than this PR, or deliberately out of scope; chip them)

### F1. PC standard minimum guarantee is below its statutory floor in April 2027 (highest-value follow-up)
SSAA 1992 s150A(2) requires the SMG to rise by at least the increase in earnings. HCWS1101 raised it 4.8% "in line with the increase in average earnings". For April 2027 that means at least 3.9%: £238.00 → about £247.30 a week, single.

The model on both main and this head gives £243.47 (+2.3%, `minimum_guarantee.yaml:17-22,38-43`). The PR flags this honestly and lists it as a follow-up.

Linked to it:
- The six HB pension-age allowances rose 4.75–4.8% in 2026 (`aged_from_cutoff` equals the SMG in every year 2021–2026).
- The savings credit threshold. The cleanest model is threshold = SMG − maximum / 60%, with the maximum by September CPI.

Recommend a chip right after this PR. Moving the SMG to `indices.triple_lock` or an earnings index changes PC aggregates materially, which is allowed as a bug fix under the merge rules.

### F2. Scottish benefits that rise by September CPI sit on other indices
- **Scottish Child Payment** (`social_security_scotland/scottish_child_payment/amount.yaml:9-18`) holds explicit 2027–2030 values from the SFC January 2026 forecast: £28.85 for April 2027 (+2.3%). At September 2026 CPI it would be £28.20 × 1.035 = £29.19, which rounds to £29.20 at the nearest 5p. Past these values it falls back to same-year calendar CPI.
- **PAWHP:** the five `pawhp/amount/*.yaml` files use same-year calendar CPI.
- **Scottish Carer Supplement** (`carer_support_payment/supplement.yaml`) has no `uprating`, so £11.70 is frozen from 2027.

The model's own SSI-sourced values show SCP and PAWHP rose exactly by September CPI in 2025 (1.7%) and 2026 (3.8%). Social Security (Scotland) Act 2018 s86A leaves "relevant prices" to the Scottish Ministers, so this is practice, not statute.

The PR moved IIDB off same-year CPI; these deserve the same treatment, with the SCP forecast values replaced once Scottish Ministers set the 2027-28 rates.

### F3. ESA(IR) personal allowances and contribution-based JSA amounts have no `uprating`
`gov.dwp.ESA.income.amount_*` and `couple`, and `gov.dwp.JSA.contrib.amount_*`, stay at their 2026 values for ever. No formula reads them (ESA(IR) is a screened reported award, `esa_income.py`), so there is no output effect today.

Under UC Act 2025 s5(1) the ESA(IR) personal allowance follows the s1 standard-allowance rule. The model's 97.75 for 2026 = 92.05 × 1.038 × 1.023. JSA(C) is a September CPI amount (2026: +3.8%). These belong with the PR's "UC Act 2025 s5" follow-up.

### F4. Rounding
Benefit parameters carry no `rounding`, so projected rates are unrounded. Against DWP rounding, the differences are 2.5p a week or less: CA £89.4756 against £89.50, CB additional £18.5265 against £18.55. That is acceptable for a projection, and noted only so nobody reads the table below as DWP's figures.

## 1. Law and practice by parameter family

I read the following this session:
- SSAA 1992 s150 and s150A (legislation.gov.uk XML).
- UC Act 2025 ss1, 4 and 5.
- Social Security (Scotland) Act 2018 s86A.
- HCWS1101, through the Parliament written-statements API (id 1857204).

I did not open the SI 2026/148 EM myself. HCWS1101 states the same basis: "increased by 3.8%, in line with the increase in the consumer prices index in the year to September 2025".

Practice check: for every parameter on the benefit index or on lagged CPI, I compared the YAML's April-to-April change, 2021–2026, with that year's September CPI. A year passes if published = previous × (1 + CPI) within 5p or 0.11%.

| Family (head) | Basis | Practice 2021–26 | Verdict |
|---|---|---|---|
| CA, AA, DLA, PIP, SDA, IIDB, CAA (s150(3): must rise at least by prices) | s150(2)(a), September CPI | all years pass | correct on the index; IIDB fixed off same-year CPI |
| IS, JSA(IB), HB working-age allowances, disability/carer premia, PC additions, UC child/carer/disabled child/work allowance/housing non-dep (s150(1)(h),(k),(l),(n); discretionary s150(2)(b)) | September CPI by practice | all pass (UC first-child higher amount and PC child additions deviate in 2022–24, then follow CPI in 2025–26) | correct |
| Child Benefit (s150(1)(i)) | September CPI by practice | pass | correct |
| Carer Support Payment (Scotland) | s86A, September CPI by practice | pass 2025–26 | correct |
| Tax credits | inactive from 2025 | n/a | harmless |
| UC standard allowance, LCWRA (UC Act 2025 ss1, 3, 4; s150 disapplied) | September CPI plus uplift; s4 floor | 2027 single 25+ £443.21 = Act minimum (400.14 × 1.038 × 1.035 × 1.031 = 443.208) | correct |
| UC childcare cap | September CPI by practice | pass 2024–26 | **B2: frozen** |
| HB non-dep deduction **thresholds** | earnings by practice | fail every year from 2019 except 2022 | **S1** |
| PC SMG (s150A) | ≥ earnings; 4.8% in 2026 | not CPI | correctly kept off; **F1** |
| PC savings credit threshold (s150(1)(l)) | derived: SMG − max/0.6, max by CPI | not CPI | correctly kept off; wording **S2**; **F1** |
| HB pension-age `aged` and `aged_from_cutoff` (s150(1)(h)) | track SMG and earnings | not CPI | correctly kept off; wording **S2**; **F1** |
| DfE early years funding rates | DfE annual funding formula | +2.9–8.0%, not CPI | correctly kept off; **B1** test |
| Council tax high value surcharge (from 2028) | not social security | n/a | kept as before; fine as a placeholder |
| SCP, PAWHP, Scottish Carer Supplement | s86A, September CPI by practice | pass 2025–26 | **F2** (not on the index) |
| Benefit cap, LHA | held (HCWS1101) | n/a | not on the index; correct |

## 2. The ONS figure

The ONS time-series API (`/timeseries/d7g7/mm23/data`) has `releaseDate` 2026-10-20T23:00Z, which is 21 October BST. "2026 SEP" = **3.5**.

Every September 2010–2025 value in `statutory_uprating_inputs/cpi_september.yaml` also matches D7G7. The new entry is `2026-09-01: 0.035` with the null moved to `2027-09-01` (`cpi_september.yaml:23-27`). That is the right file, the right date key (observation month, `preserve_calendar_dates`) and the right unit.

`yoy_growth.september_cpi_uprating` gives 0.035 for 2027-01-01. The index ratio 2027/2026 is 1.034998 (the 5 dp index rounding leaves less than 0.0002% of noise). The `forecast_gap.cpi_september` value for 2026 (−0.00184) is now unused, as designed.

## 3. Interaction with the triple lock

ONS KAC3 (20 October release) gives May–July 2026 = 3.9%. So for April 2027 the triple lock is max(3.9%, 3.5%, 2.5%) = 3.9%, and earnings binds.

The model gives:
- new State Pension £241.30 → £250.711 (+3.900%);
- basic State Pension £184.90 → £192.111 (+3.900%).

Both are identical on base and head. DWP's 5p rounding would give £250.70 and £192.10.

`test_the_triple_lock_reads_the_same_september_cpi` ties the triple lock's CPI element to the same rounded figure.

**Additional State Pension (#2336):** `additional_state_pension.py:79-82` uprates by `indices.september_cpi_uprating`. Its April 2027 rise is now 3.5% (index ratio 1.034998), against base 2.1% (the OBR forecast it replaces, ratio 1.021000). That is the +£189.7m State Pension line in the impact report.

## 4. Rates spot-check (April 2027, weekly unless stated)

Values are read at 30 April. "DWP-rounded" is the 2026-27 rate × 1.035, rounded the way DWP rounds that benefit.

| Rate | 2026-27 | Base 582b86315 | Head d8aae1b12 | DWP-rounded | Head vs DWP-rounded |
|---|---:|---:|---:|---:|---:|
| Carer's Allowance | 86.45 | 88.4382 | 89.4756 | 89.50 (5p) | −2.4p |
| PIP daily living, enhanced (also AA higher, DLA care highest) | 114.60 | 117.2355 | 118.6108 | 118.60 (5p) | +1.1p |
| Child Benefit, eldest | 27.05 | 27.6721 | 27.9967 | 28.00 (5p) | −0.3p |
| UC child element (month) | 303.94 | 310.9299 | 314.5774 | 314.58 (1p) | 0 |
| IIDB 100% | 233.90 | 238.5776 (same-year CPI, 2.0%) | 242.0861 | 242.10 (10p) | −1.4p |
| Also checked: UC carer element (month) | 209.34 | 214.1544 | 216.6666 | 216.67 | 0 |
| JSA(IB) / IS 25+ | 95.55 | 97.7474 | 98.8941 | 98.90 | −0.6p |
| SDA | 119.35 | 122.0948 | 123.5271 | 123.55 | −2.3p |
| PC severe disability addition | 86.05 | 88.0290 | 89.0616 | 89.05 | +1.2p |
| UC standard allowance, single 25+ (month) | 424.90 | 438.0710 | 443.2099 | 443.21 (Act s1 minimum) | 0 |
| PC SMG, single | 238.00 | 243.4735 | 243.4735 | ≥247.28 (s150A, earnings) | F1 |
| UC childcare cap, 1 child (month) | 1,071.09 | 1,071.09 | 1,071.09 | 1,108.58 | B2 |

All of the PR body's rate table matches these values.

## 5. Tests

The load rule was kept. A first run started at load 172 was stopped, and the later runs waited for load1 < 110. All runs used `-n 2`, `uv run --frozen` and `-p no:cacheprovider`.

- **Batch 1:** `test_september_cpi_uprating.py`, `test_september_cpi_uprating_properties.py`, `test_benefit_uprating_published.py`, `test_triple_lock_statutory_inputs.py`: **69 passed** (795 s).
- **Batch 2:** `test_childcare_funding_rates.py`, `test_triple_lock_properties.py`, `test_triple_lock_outturn.py`, `test_dwp_published_rates.py`, `test_state_pension_components.py`: **1 failed, 1395 passed, 60 skipped** (1647 s). The failure is B1, reproduced on the head.
- **Batch 3:** `test_uc_standard_allowance_uplift.py`, `test_uc_health_element_freeze.py`, `test_uc_rebalancing.py`: **72 passed** (2013 s).
- **Benefit-rate YAML:** `policyengine-core test` over `tests/policy/baseline/gov/dwp`, `gov/social_security_scotland` and `finance/benefit` (198 files): **2126 passed** (476 s).
- **CI YAML suite** (all of `tests/policy`): pass.

## 6. CI and aggregate impact

`gh pr checks 2557` (final):
- **Fail:** Test / Python 1/5 (B1: 1 failed, 1565 passed, 10 skipped, 2 xfailed), and so the Test / Result roll-up.
- **Pass:** Python 2/5–5/5, YAML, Lint, docs builds, the four smoke-imports, Changes, Fix evidence, Aggregate impact.

`mergeable` = MERGEABLE (not a draft).

The aggregate impact bot compares base main `9d81a5dfa` with head `28632cd8c`, which is #2557 merged into main. Data: `enhanced_frs_2024_25.h5`, sha256 `056e80fd8e91`. Results for **2027-28**:

| Measure | Change | Direction check |
|---|---:|---|
| Universal Credit | **+£868.9m** (£84.93bn → £85.79bn) | up, as expected: CPI-linked elements +3.5% against +2.3%, standard allowance +4.31% against +3.1%; LCWRA and housing unchanged |
| Pension Credit | **+£23.2m** | small rise, plausible: SMG unchanged; the carer and severe disability additions rise 3.5%; the higher additional SP is income to PC. I did not decompose it |
| Total benefit spending (`gov_spending` / `household_benefits`) | **+£1.88bn** | up, as expected |
| State Pension | +£189.7m | additional SP at 3.5% against 2.1%; triple lock unchanged |
| PIP, CB, AA, DLA, CA | +£339.5m, +£203.2m, +£109.4m, +£94.4m, +£56.4m | about +1.17% of each line: 1.035 / 1.023 − 1 |
| HB, CTR, WFP | −£2.9m, −£0.6m, −£0.5m | small; not traced |
| Income tax | +£66.4m | taxable benefits (SP, CA) up |
| Government balance | −£1.82bn | |

2025-26 and 2026-27 are zero in every line, as expected: every live amount has an explicit 2026 value. 57.6% of people gain more than £1 in 2027-28 and 0.6% lose more than £1 (not traced). Absolute child poverty after housing costs falls 0.44pp. The one check failing on both sides (negative VAT for 76 units) is unrelated.

After B2 the UC line will rise slightly further, from the childcare cap. The bot's next run will show by how much.

## What to change before merge

1. B1: update `test_childcare_funding_rates.py:161` to the lagged CPI factor.
2. B2: add `propagate_metadata_to_children: true` to `childcare/cap.yaml`, and extend the index test to fail on node-level `uprating` that doesn't reach its leaves.
3. S1–S3 (and S4 if this PR owns it): flag the HB non-dep thresholds as earnings-linked, fix the "outside the s150 review" wording, and fix the docstring.

Then a re-review of the delta and a green CI (`gh pr checks` exit 0) at the new head. F1–F4 go to chips: F1 first, then the Scottish set and ESA/JSA(C).
