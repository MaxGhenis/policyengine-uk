VERDICT: REQUEST_CHANGES
Head reviewed: 9b0d406723d172e8a07c0ef42d57fd010251b977

Two P2 findings remain despite green required checks: maximum Savings Credit reforms lose effects that main supports, and the new Pension Credit documentation is excluded from publication. The enacted rates and the other projection/reform safeguards check out.

Reviewed the brief, hand-off, PR body, every conversation comment, all three reviews, the empty inline-comment list, all 24 files returned by `compare/eb0b8087d...9b0d40672`, relevant files at both parents, workflow definitions and complete CI logs. Main is `eb0b8087d821b92d4faa75cf51a92d15aa2a3c45`; the old PR is `52c96b111efe3205feae501aafce869977dba02c`. These are the actual merge parents, in PR/main order. GitHub reports draft, MERGEABLE, UNSTABLE.

**P2 — Preserve main's response to maximum Savings Credit reforms.** `policyengine_uk/parameters/gov/dwp/pension_credit/savings_credit/create_savings_credit_threshold.py:302` and `policyengine_uk/parameters/gov/dwp/housing_benefit/allowances/create_pension_age_allowances.py:229`.

Both builders call `enacted_maximum(projection_base, ...)`, where reforms supply the unreformed tree as `projection_base`. They never use the reformed maximum's amount or its future anchors to generate the indices. This goes beyond the documented independence from guarantee and phase-in reforms. Main explicitly reads the live, already-uprated maximum in threshold builder lines 58–65 and HB builder lines 35–39. The unchanged `savings_credit/maximum.yaml:1` still describes it as the maximum used to derive projected thresholds.

For example, with maximum.SINGLE permanently zero from April 2026, main's 2027 guarantee, threshold and higher single/lone-parent HB allowance are all £247.282. This head leaves the threshold at £216.301 and higher HB at £265.8706, although the maximum parameter itself is zero. The Savings Credit payment formula derives its cap from guarantee minus threshold, so it still permits a positive maximum award. These numbers follow directly from the source and the CI-pinned 2027 inputs; this counterexample was not executed locally. Future maximum anchors have the same omission.

Required replacement behavior: retain unreformed guarantee/phase-in context, but consume the reformed maximum's complete independently uprated timeline when the threshold/allowance's own base has not changed. Keep the existing own-base reform fallback. Replacing the two calls with `enacted_maximum(parameters, ...)` alone is insufficient because it still ignores later anchors.

Exact proposed insertion into `test_pension_age_projection_invariants.py`, using its existing helpers/imports, supplies an independent zero-maximum oracle:

```python
@pytest.mark.parametrize("first_year", [2026, 2028])
def test_maximum_reforms_reach_both_dependent_forecasts(first_year):
    parameters = synthetic_parameter_tree([(0.039, 0.035)])
    unreformed = parameters.clone()
    parameters.get_child(f"{SC_NAME}.maximum.SINGLE").update(
        start=f"{first_year}-04-01", value=0
    )
    projected = project_synthetic_parameters(parameters, unreformed)
    for year in range(max(first_year, FIRST_PROJECTION_YEAR), LAST_INDEX_YEAR + 1):
        at = f"{year}-04-30"
        guarantee = projected.get_child(f"{SMG_NAME}.SINGLE")(at)
        assert projected.get_child(f"{SC_NAME}.maximum.SINGLE")(at) == 0
        assert projected.get_child(f"{SC_NAME}.threshold.SINGLE")(at) == pytest.approx(
            guarantee
        )
        for kind in ("single", "lone_parent"):
            assert projected.get_child(f"{HB_NAME}.{kind}.aged")(at) == pytest.approx(
                guarantee
            )
```

One concrete production replacement uses Core's existing anchor rules on a private maximum clone. Add this helper/import to the threshold builder:

```python
from policyengine_core.parameters.operations.uprate_parameters import uprate_parameters


def projected_maximum_values(maximum, price_index, base_year, final_year):
    projection = ParameterNode(name="maximum_forecast", data={})
    projected = maximum.clone()
    projected.metadata["uprating"] = "index"
    projection.add_child("maximum", projected)
    projection.add_child("index", price_index.clone())
    uprate_parameters(projection)
    return {
        year: max(0, float(projected(projection_instant(year))))
        for year in range(base_year + 1, final_year + 1)
    }
```

Pass an optional `maxima=None` through both `_projection_parameter` functions into their index helpers. Before each wrapper's own-base comparison, compute it with `projected_maximum_values(parameters.gov.dwp.pension_credit.savings_credit.maximum.children[relationship], price_index, base_year, final_observation_year + 1)`; set it to `None` inside the existing changed-own-base branch. Import the helper in the HB module. Replace threshold index line 93 with:

```python
        maximum = (
            maxima[year]
            if maxima is not None
            else project_maximum_savings_credit(maximum, growth)
        )
```

Replace protected-allowance index line 79 with:

```python
        retained_uplift = (
            maxima[year]
            if maxima is not None
            else project_retained_uplift(retained_uplift, growth)
        )
```

These are proposed changes, not validated patches. Cover both public reform/scenario interfaces, base-year and future anchors, and combinations with own-base reforms before merging. The existing combined strategy omits maximum paths, and its differential oracle only exercises unreformed macro paths; consequently green CI does not settle this regression.

**P2 — Publish the newly linked Pension Credit page.** `docs/book/programs/gov/dwp/state-pension.md:263`, with the missing registration at `myst.yml:41`.

The added link targets `pension-credit.ipynb#uprating`, but Programmes includes only the carbon-tax notebook and a `*.md` pattern. `myst.yml:22` explicitly says notebooks are not pattern-matched. The successful [documentation build](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127513932) lists 50 built pages, including State Pension, and never builds Pension Credit. The link does not auto-include the notebook. Vahid's placement nit is therefore incomplete for published readers.

Replace the Programmes block at `myst.yml:38` exactly with:

```yaml
    - title: Programmes
      children:
      - file: docs/book/programs/contrib/ubi-center/carbon-tax.ipynb
      - file: docs/book/programs/gov/dwp/pension-credit.ipynb
      - pattern: docs/book/programs/gov/*/*.md
```

Rebuild docs and verify the Pension Credit page and incoming Uprating link. Current CI proves the selected pages build, not that this page is selected.

**P3 — Refresh the PR's evidence statement.** PR description lines 32–34.

The zero-local-tests statement is accurate, but saying the suites remain for CI and runtime validation is pending is stale. Replace those two paragraphs with:

```text
Runtime tests: 0 executed locally because the build's host resource gate closed. CI at 9b0d406723d172e8a07c0ef42d57fd010251b977 passed 4,911 policy YAML cases and audited all 10,201 collected Python tests: 10,138 passed, 61 allowlisted skips and 2 allowlisted xfails, including all six 13 October regressions. Required Test / Result and Lint pass. The configured documentation build passed; it did not include the Pension Credit notebook. No local mutation testing or microsimulation was run.

Aggregate impact timed out after 60 minutes before producing a comparison, so no aggregate estimate is available for this head. Prior aggregate reports predate this merge.
```

**P3 — Replace the external-contributor Axiom placeholder with the reconciliation's actual scope.** PR description line 38.

`docs/engineering/skills/github-prs.md` reserves `axiom: needed` for external contributors who cannot complete parity work. The author and hub are members. Relative to main, the retained changes are forecast generation, reform safeguards, references and coverage; this review found no new enacted amount or legal rule requiring a fresh encoding. Replace the line with:

```text
axiom: n/a: this reconciliation changes forecast generation, reform safeguards and regression coverage only; main already contains the enacted Pension Credit and Housing Benefit rates and legal uprating rules.
```

Do not claim `encoded-correct`, a new encoding or a queued issue without evidence. This scope statement does not assert that main's existing parity work is complete.

The merge-resolution audit follows the hand-off's DIFFERENCES rows. Paths in this table are under `policyengine_uk/`; PC means `parameters/gov/dwp/pension_credit`, HB means `parameters/gov/dwp/housing_benefit/allowances`.

| Row | Main versus old PR; actual merged result and judgment |
| --- | --- |
| Earnings series | Main `parameters/gov/economic_assumptions/create_earnings_uprating.py:34` floors the published-precision statutory input and compounds without rounding the index. PR `parameters/gov/dwp/state_pension/triple_lock/create_triple_lock.py:154` duplicates this floor/series. Head retains main byte-for-byte and drops the duplicate. Correct. |
| Threshold algorithm | Main `PC/savings_credit/create_savings_credit_threshold.py:58` uses the published maximum after uprating. PR `PC/create_savings_credit_threshold_projection.py:75` uses the rounded guarantee–threshold gap and generates an index. Head uses main's published maximum/algebra through PR-style indices. Correct unreformed; maximum-reform loss is finding 1. |
| Phase-in zero/independence | Main's live zero rate retains the previous threshold; PR takes the enacted rate and isolates phase-in reforms. Head keeps enacted zero handling while insulating separately set thresholds/HB from phase-in reforms. This intentional difference is documented and tested. |
| Higher HB formula | Main `HB/create_pension_age_allowances.py:35` uses guarantee plus published maximum; PR `HB/create_protected_pension_age_uprating.py:46` compounds HB minus guarantee. Head retains main's exact unreformed forecast sum, preserving independently rounded enacted HB. Correct. |
| HB reform guards/indices | Main derives directly from live components; PR supplies independent per-allowance indices and below-guarantee/zero fallbacks. Head retains those extras and guarantee-only independence. Correct for documented reforms, except the unrequested maximum independence. |
| Common base | Main extends each parameter from its own last explicit value; PR validates seven paths. Head `PC/pension_age_projection_base.py:14` validates the raw/unreformed seven-path tree and lists paths/years on disagreement. Correct. |
| CPI/threshold floors | Main already floors CPI for published maxima; PR also floors CPI. Head keeps that existing mechanism and adds the threshold residual floor, with finite positive index bounds to support later anchors. No duplicate CPI mechanism. |
| Higher HB history/2025 citations | Main supplies #2207's 2015–19 history and correct 2025 rates; PR adds dated GB/NI citations but has wrong 2015 placeholders. Head preserves main history plus citations. Independently verified below. |
| `aged_from_cutoff` | Main uses earnings; PR uses its duplicate earnings-floor series. Head retains main's common earnings route, unchanged from main. Unreformed lower allowances remain equal to the guarantee. Correct. |
| Guarantee YAML | Main uses earnings and published history; PR uses its duplicate series plus citations. Head keeps main's route/values and adds citations/forecast wording. Correct. |
| Threshold YAML | Main has post-uprating generation; PR has index metadata and independence wording. Head adds index metadata and retains published anchors/wording. Correct, subject to finding 1. |
| System orchestration | Main's builders run after uprating; PR's run in generation. Head registers the two existing modules once before uprating and passes unreformed context into prior-law rebuilding. Required indices already exist; no duplicate invocation. |
| Guarantee YAML tests | Main has two 2026 cases plus two 2027 earnings cases; PR has two 2026 plus two 2025 cases. Head retains all six. The hand-off's claim that this main file already had additional 2025 cases is inaccurate; the resolution is correct. |
| September CPI tests | Head is unchanged from main. Pension-age paths, including the later cohort, remain excluded from inappropriate lagged-CPI expectations. Correct. |
| Projection tests | Main's 34-test file remains, with intentional reform/floor expectation updates. PR's distinct published-rate, base, guard and continuity tests survive; four new Hypothesis/differential contracts supplement them. Coverage gap: maximum reforms. |
| Documentation | Main's dedicated PC README remains and is expanded; PR's State Pension explanation becomes a link to the PC notebook's new Uprating section. Source placement is improved, but publication is missing: finding 2. |
| Changelogs | `2072.fixed.md`, `2083.fixed.md`, `2154.fixed.md` are absent at head. `2092.fixed.md:1` now describes floors, reform safety, common-base validation and continuity. No duplicate main-law change is added relative to main. Correct. |

Every file changed relative to main was read. The table covers both builders, five parameter YAML files, base helper, system, README, notebook/State Pension docs, changelog and projection test files. The remaining changed tests are the protected-rate YAML, guarantee/eligibility/award YAML, process-time inventory and statutory-input tests; their additions preserve main's distinct cases and add focused independent published-rate/payment assertions. No other loss from main was identified.

The published-value and law audit used independently fetched legislation XML and DWP rates, not the hand-off's quotations. All 104 explicit records on main across the nine relevant parameter files are preserved exactly. All 90 old-PR records are preserved except these three documented same-date corrections:

| Higher HB file, under HB | Date | Old PR | Main/head | Where the old amount correctly survives |
| --- | --- | ---: | ---: | --- |
| `single/aged.yaml:10` | 2015-04-01 | £181 | £166.05 | 2019-04-01, line 30 |
| `lone_parent/aged.yaml:10` | 2015-04-01 | £181 | £166.05 | 2019-04-01, line 30 |
| `couple/aged.yaml:10` | 2015-04-01 | £270.60 | £248.30 | 2019-04-01, line 30 |

[SI 2015/457 Schedule 7](https://www.legislation.gov.uk/uksi/2015/457/schedule/7/made), table 1(1)(b)/1(2)(b), and [DWP 2015–16 rates, page 7](https://assets.publishing.service.gov.uk/media/5a7eac8fed915d74e33f1b40/proposed_benefit_and_pension_rates_2015_to_2016.pdf#page=7) establish £166.05/£248.30. [SI 2019/480 Schedule 4](https://www.legislation.gov.uk/uksi/2019/480/schedule/4/made) and [DWP 2019–20 rates](https://www.gov.uk/government/publications/benefit-and-pension-rates-2019-to-2020/proposed-benefit-and-pension-rates-2019-to-2020#housing-benefit) establish £181/£270.60. Preserving the three original 2015 placeholders would be wrong.

[SI 2025/295 Schedule 6](https://www.legislation.gov.uk/uksi/2025/295/schedule/6/made) and [DWP 2025–26 rates](https://www.gov.uk/government/publications/benefit-and-pension-rates-2025-to-2026/benefit-and-pension-rates-2025-to-2026) independently establish higher HB £244.40/£366, guarantee £227.10/£346.60, threshold £198.27/£314.34 and maximum Savings Credit £17.30/**£19.36**. The brief's £19.35 is inaccurate. Published couple HB remains £366, independently rounded; it must not be replaced with the £365.96 component sum. The exact sum invariant appropriately applies after enacted rates. The retained 2026 anchors also match [DWP 2026–27 rates](https://www.gov.uk/government/publications/benefit-and-pension-rates-2026-to-2027/proposed-benefit-and-pension-rates-2026-to-2027).

[SSAA 1992 s150A](https://www.legislation.gov.uk/ukpga/1992/5/section/150A), particularly (1)(d), (2), (3), (4), (8), supports an earnings minimum for the guarantee, with measurement/rounding discretion; no CPI/2.5% triple-lock element is required. The separate earnings floor is defensible. [SPCA 2002 s3](https://www.legislation.gov.uk/ukpga/2002/16/section/3)(4),(7), with [regulation 7](https://www.legislation.gov.uk/uksi/2002/1792/regulation/7), supports deriving the threshold from the guarantee, maximum and prescribed 60% rate. CPI projection of the maximum is a forecast convention consistent with the current [uprating statement](https://questions-statements.parliament.uk/written-statements/detail/2025-11-26/hcws1101), rather than an immutable rule in s3.

[DWP A3/2021 paragraphs 3–5](https://www.gov.uk/government/publications/housing-benefit-adjudication-circulars-2021/a32021-housing-benefit-person-who-have-attained-the-qualifying-age-for-state-pension-credit-amendment-regulations-2021) supports higher HB based on guarantee plus maximum Savings Credit and the later cohort's omission of the uplift. [SI 2021/188 regulation 2](https://www.legislation.gov.uk/uksi/2021/188/regulation/2/made) confirms the 1 April 2021 cutoff and lower rates. Keeping the same earnings index preserves their unreformed equality. Floors, common-base checks, independent reform handling and the own lone-parent index are defensible modelling/engineering choices. No legal or enacted-rate contradiction was found.

The invariant tests are meaningful beyond formula restatements. The combined Hypothesis property tests successful construction/non-negativity; the HB identity compares distinct output parameters; the differential freezes main's different post-uprating implementation. The enacted preservation test draws expectations from raw YAML, proving no overwrite rather than independent legal correctness; hard-coded source-based rate/payment cases and the external audit supply the latter. The 2035 boundary regression independently locates the single/couple Guarantee Credit cutoff and checks HB, CTR and income continuity.

Coverage limits: combined reforms cover finite non-negative amounts capped at 1e100 and rates at 100, one anchor per path, and omit maximum Savings Credit. They do not establish the body’s no-raise statement over every finite combination. Enacted preservation samples entries rather than enumerating all of them. Negative explicit monetary reforms and arbitrary multiple-anchor combinations are not established by these properties. No additional production defect is inferred solely from those limits.

Builder order is safe on inspection: statutory inputs, earnings, triple lock, September CPI and economic indices precede both builders (`tax_benefit_system.py:129`); both use the concrete generated CPI index rather than its unresolved YAML alias. Each builder appears once in `GENERATION_STEPS`; the old post-uprating calls were removed. Baseline processing uses a separate unreformed tree, and prior-law fixed-point processing uses fresh clones, so these are not duplicate applications to one tree. The seven-path base is read before general uprating and from unreformed context during reforms. Guarantees/phase-in leave independent thresholds/HB intact; own threshold/allowance changes anchor forecasts; zero/below-guarantee bases build and preserve explicit values. These documented contracts passed CI.

CI evidence is from [Code changes run 40179559025](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025). Every current run reports this head SHA. The runtime checkout is GitHub's synthetic merge `543f63289e1e2aa758be37036a3e69de24e6822f`, verified to have exactly the reviewed head's tree `83b7c5b72fac6c305edd12c66f93675d6ee51a63`. Thus these are current-source results, not old-branch results. Ruleset 24934210 requires Test / Result and Lint; both pass. Changelog, Fix evidence, docs and Python 3.11–3.14 smoke checks also pass.

| CI job | Result |
| --- | --- |
| [YAML](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514019) | 4,911 passed |
| [Python 1/5](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514065) | 1,977 passed; 10 skipped; 2 xfailed |
| [Python 2/5](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514044) | 2,073 passed; 14 skipped |
| [Python 3/5](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514078) | 2,026 passed; 14 skipped |
| [Python 4/5](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514057) | 2,014 passed; 11 skipped |
| [Python 5/5](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121127514030) | 2,048 passed; 12 skipped |
| [Result](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179559025/job/121141662734) | All 10,201 collected tests assigned exactly once; 10,138 passed, 61 allowlisted skips, 2 allowlisted xfails; zero skipped/failed modules; dataset present |

All files on the hand-off's Python “Not run” list have explicit PASSED records: `test_pension_age_projection_invariants.py` 4; `test_pension_credit_uprating.py` 34; `test_housing_benefit_protected_allowance_uprating.py` 13; `test_pension_credit_guarantee_reform_projections.py` 39; `test_savings_credit_threshold_projection.py` 14; `test_september_cpi_uprating.py` 17; `test_triple_lock_statutory_inputs.py` 23; `test_process_time_reforms.py` 71; `test_council_tax_reduction_pension_credit_properties.py` 9; `test_savings_credit_only_receipt_properties.py` 6. These are test nodes, not Hypothesis example counts. The four new contracts ran in shards 5 (combined reforms), 2 (identity and enacted preservation), and 1 (main differential).

YAML logs include all 27 Pension Credit files/320 cases, 40 principal HB files/456 cases and seven integration files/54 cases. Specifically, #2576's `pension_age_earnings_uprating.yaml` has six passes and `council_tax_reduction_pension_age_personal_allowance.yaml` ten; `protected_pension_age_rates.yaml` has two and `standard_minimum_guarantee.yaml` six.

Vahid's open points map to these current-head results:

| Point | Resolution and explicit CI evidence |
| --- | --- |
| 2025–26 HB amounts | Resolved: `test_protected_allowances_match_enacted_2025_amounts` single/lone-parent/couple passed shards 1/2/3, plus both protected-rate YAML cases. |
| Derived base year | Resolved: `test_projection_base_year_is_the_last_enacted_year` shard 1; `test_next_year_rates_move_the_projection_base` shard 4; all three `test_rates_update_that_misses_a_parameter_raises` cases shards 1/3/5. |
| 13 Oct base-year guard | Resolved: four `test_2026_guarantee_reform_pays_the_reformed_credit_without_rebuilding_hb` cases passed shards 1/4/5; below-guarantee and zero-base regressions and combined property also passed. |
| Original six CI failures | All passed: CTR `test_awards_follow_the_pension_credit_routes` and `test_freeze_keeps_savings_credit_only_receipt_when_the_reform_adds_guarantee_credit` shard 1; `test_guarantee_credit_recipients_ctr_is_invariant_to_state_pension` shard 3; `test_guarantee_credit_recipients_ctr_is_invariant_to_savings` and `test_not_claiming_pension_credit_never_raises_a_recipients_ctr` shard 4; SC-only `test_pension_credit_freeze_keeps_the_baseline_receipt` shard 2. |
| Nit 3 | Resolved: independence sentence in `threshold.yaml:6`/README; `test_phase_in_reform_changes_savings_credit_not_the_projections` passed shards 1/4 and guarantee independence tests passed across shards. |
| Docs placement | Source section/link added, but not published. Docs CI passed without building the notebook: finding 2. |

The [8 October CHANGES_REQUESTED](https://github.com/PolicyEngine/policyengine-uk/pull/2092#pullrequestreview-5455984817) remains formally open; the [13 October follow-up](https://github.com/PolicyEngine/policyengine-uk/pull/2092#pullrequestreview-5500868783) has no subsequent approval. This review does not dismiss either.

[Aggregate impact run 40179558930](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40179558930/job/121127479161) was cancelled at its 60-minute timeout. It measured 220 base figures in 1,876.11 seconds, then was cancelled during head computation before comparison. The bot reports no report. This is not a required check, but there is no current-head aggregate estimate to validate. The body correctly avoids using older estimates; its pending wording needs finding 3's update.

The body starts with `Fixes #2083`, satisfying the required first-line form, and states the four requested invariants. It accurately distinguishes forecast from independently rounded enacted values. The changes description should retain that distinction and the maximum-reform caveat until finding 1 is fixed. The rewritten 2092 fragment is present and Changelog/Fix evidence checks pass.

No repository clone, dependency installation or local model test was needed for this review; the disk-hold file was absent at start, and CI supplied full execution evidence. No local runtime validation is claimed for the proposed fix or regression. Review-artifact validation: Markdown/code-block structure, proposed Python syntax and `git diff --check`. No push, GitHub comment or merge was performed.

Delivery: the normal worktree commit was denied because its Git index lives under the caller’s read-only checkout. The review is committed on `subfleet-uk2092-review` in workspace-local `.job/git`, descended from checkpoint `e92ff40d89bccade13ddf9a2f393143aa33b729f`. `review.bundle` contains that commit and its complete brief ancestry; the original Git metadata was not modified.
