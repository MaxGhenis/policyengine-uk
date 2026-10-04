REQUEST_CHANGES
head: cf40b021b63d3724fa58e2511f0626746cf96077

# Delta review of policyengine-uk#2119, round 2

Reviewed the fix commit 4313fbd3a against round 1 (e34b75358), and the whole PR
at cf40b021b. Merge cf40b021b changes none of the PR's 21 files, but it brings
in main's #2006, which matters for blocking finding B2. No model source was
edited in the checkout, nothing was pushed, and nothing was posted to GitHub.
All households are hand-built synthetic cases, and no survey records were
read.

The round 1 blocker is fixed, and the new destination rule matches SI 2019/167
art 3A(1). Two new problems block the merge. The non-claim branch of
`left_pension_route_at_legacy_closure` contradicts SI 2019/37 art 4(3)(b)(ii)
and DWP circular A9/2024 paras 12-13, which the variable itself cites. Separately,
main's merge brought in a new reader of `would_claim_uc`, so closure claimants
skip the UC non-dependant deduction.

## 1. Round 1 findings

| Round 1 finding | Status | Evidence at cf40b021b |
|---|---|---|
| Blocking: protected 72/40 WTC+HB couple not moved to UC | Resolved | R1-A: closed, claims, `is_uc_eligible` true, UC 13,537.20, HB 0, PC 0. R1-A' (older member earns 10,000 at 20h, `would_claim_pc` false): UC 8,037.20, HB 0, PC 0 |
| NB: tax-credit continuation reform pays UC + WTC | Cash resolved; `tax_credits` aggregate not (NB1) | R1-B (r1's exact case): UC 2,348.80, WTC 0, `tax_credits` 0. Add the child and reported CTC (R1-B'): UC 8,746.08 with `tax_credits` 3,632.44 |
| NB: `claims_universal_credit` doc overstated | Resolved | Doc now scopes the overlap and accommodation exceptions |
| NB: UC notebook take-up text | Resolved | Two claim routes; set both flags false to decline; reg 51 disregard disclosed |
| Legal: blanket "pension-age go to PC" | Resolved | reg 60A route implemented (C8, C9) |

## 2. Legal accuracy of the new code

The texts below were fetched 2026-10-03 and are saved in `review/legal/`.

- **Destination rule** (`legacy_benefits_closed.py:50-57`) is correct.
  - Art 3A(1)(a) sends a CTC-only family to Pension Credit when it is (i) single and pension age, (ii) a couple both of pension age, or (iii) a protected mixed-age couple. Art 3A(1)(b) does the same for any family on a tax credit and PC. The code's `on_pension_credit | (pension_age_route & ~WTC)` matches, since `meets_pension_credit_age_conditions` is exactly (i)-(iii) after May 2019.
  - Executed cases follow it:
    - C7, protected couple on CTC only: Pension Credit route, HB 6,000, PC 21,668.92.
    - C10, pension-age single on CTC only: PC route, HB 6,000, PC 15,597.40.
    - C11, protected couple on WTC and reporting PC: PC route, HB 6,000, PC 17,607.72.
    - C6, unprotected mixed-age couple on CTC only: UC 17,605.20, since (iii) needs the protection.
    - C5, unprotected mixed-age couple on WTC: UC 13,537.20, or nothing if it declines. This is correct, because it has no pension route.
- **Reg 60A** (`is_uc_eligible.py:50-57`) is correct.
  - A moved, wholly pension-age family is always on WTC and not on PC, so it meets 60A(1)(a)(ii)-(iii) and (1)(b).
  - C8 (single 70) gets UC 10,801.68 with HB and PC at 0. C9 (joint 70/72) gets UC 13,537.20.
  - Benefit cap: such a claim is cap-exempt through `housing_benefit_pension_age_regulations_apply`, which is consistent with reg 60C.
- **IS/JSA closures**: C13 (a pension-age single wrongly reporting IS) is not moved. C14 (a protected couple on IS+HB in 2026) moves and gets UC 14,003.64.
- **Non-claimants**:
  - A wholly pension-age non-claimant keeps the route. C8 F/F gets HB 6,000 and PC 11,536.20, which reg 6A(4) supports.
  - A protected mixed-age non-claimant does not keep it. This is B1.
- **Cycles**: none.
  - All 2,109 YAML cases and every probe computed without a cycle error.
  - The candidate fixes in section 4 add `claims_universal_credit` and `is_uc_eligible` reads without a cycle. The fix copy ran 343 YAML cases; the only failure is the B1 expectation.

## 3. Blocking findings

### B1. A protected mixed-age couple that does not claim UC loses HB and Pension Credit

**Where:** `policyengine_uk/variables/gov/dwp/pension_credit/left_pension_route_at_legacy_closure.py:29-32` (the `| is_mixed_age_couple` limb), and its documentation at lines 8-15.

**What is wrong:** a protected mixed-age couple on WTC+HB that does not claim at the closure is moved off the pension route, so it gets no HB and no PC.

**Law:**
- SI 2019/37 art 4(3) was inserted 8 June 2024 by SI 2024/604. It says that nothing in reg 6A prevents an HB claim by such a couple when:
  - (a) it has been issued a migration notice;
  - (b)(ii), "in the case of a person who did not claim universal credit", it claims within three months beginning with the day after its HB award ends;
  - (c) it meets the HB conditions.
- A9/2024 para 12: the amendments allow protected couples "to reclaim HB if they decide to not claim UC".
- A9/2024 para 13: a couple that reclaims "within three months of their previous HB claim ending" keeps "the protection", and should claim "from the Sunday before" the closure date, so no gap day ends the saving under art 4(2).
- The code comment "loses its award at the notice's deadline (reg 46(1)(a)) and with it the saving" (`housing_benefit_eligible.py:45-48`) contradicts that reading. Reg 46(1)(a) also ends HB on the last day of the two weeks beginning with the deadline day, not at the deadline itself.

**Failing input** (2025: older 72, younger 40, WTC 2,000 and HB 6,000 reported, saving true, council rent 6,000):

| Case | Model at PR head | Law, and the fix copy |
|---|---|---|
| C1: both flags false | UC 0, HB 0, PC 0 | HB 6,000, PC 17,607.72 |
| C2: `would_claim_uc` true, closure flag false | `claims_universal_credit` true, yet UC 0, HB 0, PC 0 | HB 6,000, PC 17,607.72 |

C2 is incoherent even on the PR's own terms: the family is recorded as claiming UC yet receives nothing.

**Fix:**
- Use `return moved & benunit("claims_uc_at_legacy_closure", period)`.
- Rewrite the variable's documentation, the comment at `housing_benefit_eligible.py:45-48`, and the changelog/notebook sentence.
- Change the YAML case at `claims_universal_credit.yaml:340-367` to expect `left_pension_route_at_legacy_closure: false`, `housing_benefit_eligible: true` and `is_pension_credit_eligible: true`.
- Change `test_uc_legacy_closure_properties.py:24-26` and line 216 to `left = pension_age_route and claims_at_closure`.
- Verified on a patched copy: C3 (claims) is unchanged at UC 13,537.20; C1 and C2 get HB 6,000 and PC 17,607.72. The YAML case at line 340 is the only failure, in both 39 cases (claims and sharers YAML, B1+B2 copy) and 343 cases (claims, HB folder, PC folder and mutual-exclusion YAML, B1+B2+NB2 copy). On the property files (closure, sharers, mixed-age) only the line 216-217 `left` assertion fails; the UC/PC and UC/HB exclusivity asserts and the other 10 properties pass.

### B2. Main's merge brought in a `would_claim_uc` reader, so closure claimants skip non-dependant deductions

**Where:** `policyengine_uk/variables/gov/dwp/universal_credit/housing_costs_element/non_dep_deduction/uc_non_dependants_counted.py:31`. #2006 added it on main (commit 01d140e77), and it entered the PR through merge cf40b021b. It was absent at e34b75358 and at 4313fbd3a.

**What is wrong:**
- The variable decides whether a family's UC claim counts the household's non-dependants using `would_claim_uc`.
- The PR's changelog says `claims_universal_credit` replaces `would_claim_uc` "wherever the model asks whether a family claims Universal Credit", and that is now false.
- The variable drives `uc_non_dep_deductions`, `LHA_allowed_bedrooms` and `lha_renter_has_non_dependant`.

**Failing input (N1, 2025):** head aged 40, WTC 2,000 reported, private rent 9,000 in Maidstone; non-dependant son aged 24 earning 20,000, in his own benefit unit.

| Head's claim route | Non-dependant deduction | UC bedrooms | Housing element | UC |
|---|---|---|---|---|
| `would_claim_uc` true | 1,116.24 | 2 | 7,883.76 | 12,685.44 |
| Closure claim only | 0 | 1 | 9,000 | 13,801.68 |

The closure claimant is overpaid 1,116.24 a year per non-dependant, and its bedroom count also differs.

**Fix:**
- Read `claims_universal_credit` in `uc_non_dependants_counted`. There is no cycle: `is_uc_eligible`, which the variable already reads, depends on `claims_uc_at_legacy_closure`.
- Update the reference at `test_rent_of_sharers_boarders_and_lodgers_properties.py:396`. That population sets no legacy inputs, so it passes either way and cannot catch this.
- Add N1 as a YAML case.
- Verified on a patched copy: N1 gets deduction 1,116.24, 2 bedrooms and UC 12,685.44 by either route, and all 19 sharers YAML cases pass.

## 4. Non-blocking findings

- **NB1. `tax_credits` still pays the CTC child element alongside UC (round 1's continuation finding, partly open).**
  - **Where:** `CTC_child_element.py`, which has no `is_CTC_eligible` gate. The family element and the severely disabled child element use `defined_for`, and the disabled child element multiplies by it.
  - **Effect:** `tax_credits` sums the pre-minimum amounts, so it carries the child element for any family that reports CTC but has its CTC masked. `tax_credits` is the Tax credits program variable in `programs.yaml`, and it is counted as income in HB and CTR means tests (`housing_benefit_applicable_income.py:67`, `council_tax_reduction_applicable_income.py:74`).
  - **Executed:**
    - T1, continuation reform, closure claimant on WTC+CTC+IS: UC 8,746.08, `tax_credits` 3,632.44, `child_tax_credit` 0.
    - T3, a 2024 baseline ordinary UC claimant reporting CTC: UC 8,176.44, `tax_credits` 3,455. This part predates the PR.
    - Cash is unaffected, because `household_benefits` uses the gated `child_tax_credit` and `working_tax_credit`.
  - **Why the test misses it:** the reform YAML at `claims_universal_credit.yaml:470-495` asserts `tax_credits: 0` only because its family reports no CTC.
  - **Fix:** add `defined_for = "is_CTC_eligible"` to `CTC_child_element`, and add `child_tax_credit_reported` to that YAML case.
- **NB2. A pension-route closure claimant refused UC on capital loses PC and HB (K1).**
  - **Case:** single, 70, WTC+HB, savings 20,000, closure flag true. UC 0 (`is_uc_eligible` false on capital), HB 0, PC 0. Declining gives HB 6,000 and PC 10,496.20.
  - **Law:** SI 2014/1230 reg 51 would disregard the capital over 16,000 for up to 12 assessment periods, so the claimant would actually get UC. The 0/0/0 result is an artefact of the disclosed reg 51 omission, which is why this is non-blocking.
  - **Fix:** model reg 51 for closure claimants. As a fallback, add `& is_uc_eligible` to `left_pension_route_at_legacy_closure`. Executed: K1 then gets HB 6,000 and PC 10,496.20, with no cycle, and 342 of 343 YAML cases pass; the only failure is the B1 expectation.
- **NB3. Nil-rate WTC is treated as CTC-only.**
  - A9/2024 paras 6 and 10, and reg 60A(2), treat a CTC family entitled to WTC at a nil rate as a WTC case, which goes to UC. The model reads reported WTC above 0, so it sends these families to Pension Credit.
  - The dataset probably cannot observe this. Disclose it in `legacy_benefits_closed`, or proxy it with the WTC hours test.
- **NB4. Several notes are stale now that reg 60A migrants are modelled:**
  - `meets_pension_credit_age_conditions.py:13-14` says a family on the route "is not eligible for Universal Credit".
  - `housing_benefit_pension_age_regulations_apply.py:22-27` says reg 60A migrants "are not modelled".
  - `council_tax_reduction_pensioner.py:46-51` says the same. Its test also disregards a reg 60A award in every nation; by its own comment that is right for England and for Wales from 2026-27, but not for Scotland.
  - `test_mixed_age_couple_properties.py:14-15`: P3 is now false for closure claimants. It passes only because that generator never reports tax credits.
- **NB5. Misattributed authority (nit).** The changelog and notebook credit reg 60A for protected mixed-age couples' UC claims. Those couples qualify under UC Regs 2013 reg 3(2)(a); reg 60A covers only claimants who are all over pension age.
- **NB6. The flag can put pension-age claimants on the worse option.** C12: a single person aged 70 on WTC earning 15,000 gets UC 4,618.98 if it claims at closure, against HB 6,619.86 if it declines. The flag decides regardless of which pays more. Disclose this; reg 60A(3)(b) lets a claimant return to PC.

## 5. Tests and mutants

- **Policy YAML:** 2,109 passed and 0 failed, covering all 290 files under `policyengine_uk/tests/policy`. The suite ran in four shards: finance 660, gov 1,217, other baseline 141, integration and reforms 91.
- **The three property files:** 9 passed in 1:47:13 (the exact command given; the machine's load average was 60-230).
- **M1** (`legacy_benefits_closed`: `pension_credit_route = on_pension_credit | pension_age_route`, which restores the round 1 bug): CAUGHT. 4 of the 20 closure YAML cases fail (legacy_benefits_closed@2025), and `test_closure_claims_and_the_end_of_legacy_awards` fails. The falsifying example is a generated pensioner aged 89 with a child and WTC, which is not moved.
- **M2** (`is_uc_eligible`: drop the reg 60A route): CAUGHT by YAML only. 1 of 20 fails ("pension-age WTC recipient ... can claim", `is_uc_eligible`). The closure properties pass 4/4 under M2. The property suite never asserts that a pension-route closure claimant is UC-eligible; add that property: closed, closure flag true, on the pension route and capital within the limit imply `is_uc_eligible`.
- **CI at cf40b021b:** all 7 checks pass, and GitHub reports MERGEABLE.

## 6. Gates

- B1 and B2 must be fixed first.
- The PR is still a draft (`isDraft: true`); mark it ready.
- Once both fixes land, re-run the closure YAML and properties, the sharers YAML, and the HB/PC folders.
