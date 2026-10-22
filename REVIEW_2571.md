VERDICT: APPROVE
Head reviewed: ff134627905190b2013a90824495cfc7c37fa2df

Independent review of PolicyEngine/policyengine-uk#2571 ("Project labelled energy inputs from their declared price year", refs #2526) for the UK hub. I read the projection, labelling, filtering and reset code, wrote and ran Hypothesis property tests and simulation-level checks, ran the energy, VAT and dataset-loading suites, and compared one behaviour against the base commit 2f1606e99. The code does what the PR says, nothing projects twice, and CI is green and the PR is mergeable at this head.

None of the findings block this PR. They do bear on the Budget: **this PR alone does not change any Microcosm Budget number.** Microcosm `main` does not yet write the declaration (finding 2). Once it does, the projection uses generic CPI, not an energy-price index (finding 1).

## Findings (ranked; none blocking)

1. **CPI is a proxy for energy prices, and no better ready-made index exists in the model.** Code: `policyengine_uk/data/economic_assumptions.py:140` (`ENERGY_PRICE_INDEX` = OBR CPI index) and `:380-413` (`uprate_energy`). The PR's README and docs state the limitation. Comparison computed from the repo's own parameter files:
   - **CPI:** I2026/I2024 = 1.0578, I2027/I2024 = 1.0789.
   - **Ofgem cap, full year:** `gov/ofgem/energy_price_cap.yaml` (GB typical dual-fuel bill) averages £1,725.8 in CY2024 and £1,678.2 in FY2024-25. I restated Jul and Oct 2026 to the pre-2026 typical consumption values, using the file's own £1,663/£1,862 note, and held Jan–Mar 2027 at the Oct 2026 level (my assumption). On that basis FY2026-27 averages £1,840.3. That is 1.0664× CY2024 (0.8% above CPI) and 1.0966× FY2024-25 (3.7% above CPI).
   - **Ofgem cap, VAT window:** Oct 2026–Mar 2027 sits at 1.1179× CY2024, 5.7% above the CPI-projected level. This is the window of the 0% electricity VAT measure (#2189).
   - **So:** on these numbers, a CPI-projected base costs that measure low by roughly 1–6%, depending on the price year declared and the window. Flat 2024 prices, today's behaviour, would cost it low by about 6–11%. The PR is a clear improvement, not the final index.

   **Existing candidates in the model, neither ready:**
   - `gov.ofgem.energy_price_cap` has outturn and announced values through Oct 2026. But its own description says it is not a constant-consumption index (TDCV breaks in Oct 2023 and Jul 2026). It is dual-fuel and GB-only, has no forecast, and is read only by `variables/gov/treasury/price_cap_subsidy/monthly_epg_consumption_level.py:23`.
   - `gov.contrib.policyengine.economy.energy_bills` is a 0% switch with no reader in the code.

   **Recommended follow-up chip:** a separate electricity and gas price index, built from the TDCV-normalised cap (or DESNZ QEP unit costs) for quarters already announced, then OBR EFO energy assumptions. Swap it in at `ENERGY_PRICE_INDEX`; the declaration contract does not change.

2. **Producer and caller adoption is still open, so this PR changes nothing for Microcosm data yet.**
   - **Producer:** Microcosm `origin/main` 8b0224e06 prices energy at calendar 2024 (`packages/microcosm-build/src/microcosm/build/uk_runtime/energy_pricing.py:5`, "base-year (calendar 2024) frame"). `git grep energy_price_basis` there finds nothing, so a released file is unlabelled and stays flat.
   - **Caller:** policyengine.py `origin/main` e125aa280, `src/policyengine/tax_benefit_models/uk/model.py:337` and `:373`, rebuilds `UKSingleYearDataset(...)` from DataFrames without `energy_price_basis`. `budget_reform_population.py:343` (`_filter_year`) does the same.
     - The simulated year is still projected correctly, because `datasets.py:304` loads the file directly with `Microsimulation(dataset=source.path)`, which reads the label.
     - The other years of the multi-year dataset passed to policyengine-uk come from the unlabelled observed year, so they stay at the declared prices.
     - This is harmless for single-year outputs and wrong for any read of another year.

   Follow-up in policyengine.py: carry the declaration on `PolicyEngineUKDataset` and pass it in both rebuilds.

3. **Behaviour change for unlabelled input under `no_economic_assumptions`; it is not stated in the PR body or changelog.**
   - **Where:** `economic_assumptions.py:728-750`. Unlabelled later-year energy in an external multi-year dataset is now reset to the base year when `current_energy <= base_energy`, or when both declarations are None.
   - **Verified** with `review_2571/frozen_unlabelled_multi_year.py`. The input is a 2024 value of 100 and a 2026 value of 777, both unlabelled, under `no_economic_assumptions`. 2026 energy is 777 at base 2f1606e99 and 100 at this head. The default path gives 777 on both.
   - **Intent:** this is deliberate and tested (`tests/test_energy_reset_coherence.py:305`, id `both-unlabelled-overlap-reset-remains-flat`), described in `docs/engineering/skills/dataset-sources.md:98`, and consistent with how the reset already treats every other growth-indexed input.
   - **Scope:** single-year files (legacy EFRS, Microcosm) are unaffected, because their later years are flat copies.
   - **Ask:** one line in the changelog or PR body, since the PR body's "unlabelled ... keep their current flat projection" does not cover this path.

4. **The observation year is never re-priced, by design.**
   - **Where:** `economic_assumptions.py:262` skips the first year. `uprate_energy` stamps only projected children, at `:408-412`.
   - **Effect:** when the declared year differs from the data year, the base year keeps the declared prices. For example, an FY2026 label on 2024 data gives 2024 at FY2026-27 prices, then 2025 = ×I2025/I2026 = 0.9775, a dip.
   - **Scope:** this is documented ("the original observation remains unchanged"). It does not affect Microcosm, whose data year and price year are both 2024. Producers should keep `time_period` equal to the price year, or accept this.

5. **A declared year outside the CPI index range is clamped silently.**
   - **Where:** `energy_price_basis.py:30` accepts years 1–9999.
   - **Effect:** Core's `_uprating_index_value` returns the first level (2009 = 1.0) for any earlier year and the last level (2039 = 2.13137) for any later one. I checked this by calling it at 1, 2005, 2045 and 9999. A 2005 declaration is therefore projected as if it were 2009 prices.
   - **Suggestion:** raise an error or warn outside the index's coverage. This is minor; realistic declarations are 2023–2026.

6. **Nits.**
   - `type(period_value) is not int` (`energy_price_basis.py:30`) rejects `numpy.int64`, so a caller passing a year taken from a DataFrame gets a ValueError. The JSON route is fine.
   - `core_dataset_energy_price_basis` uses `inspect.getattr_static` (`energy_price_basis.py:101`). A Core `Dataset` subclass that declares the basis as a `@property` gets the property object, and loading fails with "must contain only period_type and period_value". Docs say "named field", so this is acceptable but undocumented.
   - `UKSingleYearDataset.from_simulation` defaults `energy_price_basis=None` (`dataset_schema.py:206-209`). Exporting a projected year that way silently drops the label. That is safe (it stays flat) but lossy.

## 1. Correctness

- **Can a labelled input be projected twice? No.** From the code:
  - `apply_uprating` recomputes every later year's energy from the first-year observation, `uprate_energy(current, first_year)` at `economic_assumptions.py:275`. That overwrites the chained value from `apply_single_year_uprating` (`:328`).
  - Each projected child is stamped `fiscal_year=<its year>` (`:408-412`), so a reloaded, filtered or copied child projects from its own year.
  - Multi-year files and DataFrames are loaded without being projected again.
  - Energy is absent from `uprating_indices.yaml` and excluded from the post-2030 fallback (`:131`).
  - Core's own variable-level CPI uprating acts only beyond the last stored year (2032), starting from that year's already-projected value.
  - Every path was confirmed by the tests listed below.
- **Can an unlabelled input change?** Not on the default path. P1, S1 (unlabelled), the PR's own tests and CI's zero-change aggregate run on `enhanced_frs_2024_25.h5` all confirm it. The one exception is finding 3.
- **Can a reset leave an amount out of step with its basis? No.** P5 ran 200 random examples (random energy column subsets and random or None declarations for the base and up to three later years). After `reset_growthfactor_uprating`, every stored later-year energy amount carries exactly the basis its year declares. No column is created and the base year is untouched.
- **Property tests (Hypothesis).** The PR had none; mine are in `policyengine_uk/tests/test_energy_projection_properties_review.py`. They are review-only and could be adopted.

  | Test | Property | Result |
  |---|---|---|
  | P1 | Unlabelled is bitwise unchanged in every projected year, including after reset; the source is not mutated | pass |
  | P2 | `apply_uprating` applied twice or three times equals applying it once (amounts and bases) | pass |
  | P3 | Project, save the year-k child to H5, reload and project again: matches a single projection | pass |
  | P4 | Projected amount = source × ∏(1+g_t) of the OBR CPI growth series from the declared year, computed independently of the generated index (rtol 2e-4); the observation year is unchanged | pass |
  | P5 | Reset coherence (above) | pass |
  | P6 | Valid declarations survive copy and single/multi-year H5 round trips; invalid ones (bad kind, out-of-range, float, bool or str year, extra keys, non-mappings) raise ValueError | pass |

- **Simulation checks.** These are in `policyengine_uk/tests/test_energy_projection_simulation_review.py`.

  | Check | What it shows | Result |
  |---|---|---|
  | S1 | A Simulation on a labelled CY or FY 2024 dataset serves source × I[y]/I[2024] for every year 2024–2036: dataset projection to 2032, then Core's CPI uprating, never both. Unlabelled stays flat to 2032, then Core's CPI as before | pass |
  | S2 | `filter_dataset(sim, 1, 2026)` carries `fiscal_year 2026`, and the rebuilt simulation matches the original in 2026–2034 | pass |
  | S3 | Saving `sim.dataset` (multi-year) and rebuilding from the file gives identical amounts | pass |

## 2. Index

- **Fiscal-year and calendar-year handling is correct to within about half a percent, and follows the model's convention.**
  - The `yoy_growth.obr.consumer_price_index` series is labelled only "year-on-year growth". Its outturn values (2022 9.07%, 2023 7.30%, 2024 2.5%) match the ONS calendar-year annual-average CPI rates as I recall them, so I treat it as calendar-year. The generated index level I[y] is dated 1 January.
  - A CY declaration therefore maps exactly. An FY declaration and the FY target year (model year y = FY y/y+1) both map to their start year, so for FY→FY the quarter shift cancels to first order.
  - For CY2024 → FY2026-27 the exact quarter-weighted target is about 0.25 × 2.0% = 0.5% higher than I2026/I2024, so CY-declared data is under-projected by about 0.5%.
  - This is the same 1 January lookup the module's post-2030 fallback uses to reproduce Core's variable uprating (`economic_assumptions.py:352-373`), and S1 confirms Core's own uprating past 2032 matches I[y]/I[2032] at 1 January. It is consistent model-wide and small next to finding 1.
- **CPI compared with an energy index:** see finding 1. CPI is the index the three variables already declare (`variables/input/consumption/energy.py`), so direct situation inputs and dataset inputs now agree. No better index exists in the model today.

## 3. Producer side (what Microcosm must write)

The contract is documented in the PR (`docs/engineering/skills/dataset-sources.md:55-111` and `parameters/gov/economic_assumptions/README.md`).

- **Single-year UK H5** (pandas HDFStore with `/person`, `/benunit`, `/household`, `/time_period`): a root HDF5 attribute named `energy_price_basis`. Its value is a JSON string of an object with exactly two keys:
  - `period_type`: `"calendar_year"` or `"fiscal_year"`.
  - `period_value`: a JSON integer, the start year for a fiscal year.
- **Example:** `h5py.File(path, "r+").attrs["energy_price_basis"] = json.dumps({"period_type": "calendar_year", "period_value": 2024}, sort_keys=True)`. Write it after the HDFStore is closed, as Microcosm already does for `populace_household_weight_kind` (`uk_runtime/national_frame.py:166-180`).
- **Value for Microcosm `main`** (calendar-2024 DESNZ QEP pricing): `{"period_type": "calendar_year", "period_value": 2024}`.
- **Value for release f9d1922c** (FY2024-25 pricing, per #2526): `{"period_type": "fiscal_year", "period_value": 2024}`. Under the start-year convention both project identically; only the provenance differs.
- **Multi-year files:** the same attribute on each `/time_period/<year>` group. A root attribute on a multi-year file is ignored.
- **Malformed values fail loudly:** a float year, a string year, extra keys (for example a `"source"` field) or non-JSON all raise ValueError at load.
- **Is it enough for the Budget cut? Not on its own.** Also needed:
  - Microcosm emits the attribute, or the Budget runner passes `energy_price_basis=` when it builds `UKSingleYearDataset` from the file.
  - Microcosm keeps `time_period` = 2024 (finding 4).
  - policyengine.py carries the label if non-target years matter (finding 2).
  - The hub accepts CPI or commissions an energy index (finding 1).
- **Smoke check after labelling:** every 2026 energy amount should be 1.0578× its 2024 value, against 1.0 today.

## 4. Tests

All runs were in the foreground with `-n 2`. Load1 was under 110 at the start of each run; free disk was 59.1 GB.

| Run | Content | Result |
|---|---|---|
| 1 | The PR's three new files, plus `code_health/test_energy_price_level.py` and `test_uprating_declarations.py` | 90 passed in 691 s |
| 2 | Review property tests P1–P6 | 7 passed in 199 s |
| 3 | Review simulation checks S1–S3 | 5 passed in 83 s |
| 4 | 19 energy, VAT, dataset-loading and uprating files, listed below | 256 passed, 1 failed in 1,526 s |
| 5 | Re-run of `test_water_uprating_properties` at load1 98 | 1 passed in 49 s |
| YAML | `vat_grossing.yaml`, then `private_school_vat`, `excise_integration`, `energy_bills_rebate/*` (3) and `energy_price_cap_subsidy` | 4 passed, then 30 passed |

- **Run 4 files:** `energy_price_cap_parameters`, `vat_grossing_legacy`, `historic_vat_rates`, `dataset_fiscal_year`, `dataset_group_order`, `dataframe_dataset`, `dataset_sources`, `simulation_dataset_sources`, `input_dataframe_export`, `no_economic_assumptions`, `projection_horizon`, `uprating_inputs_reach_data`, and the council tax, domestic rates, residential property, road fuel, water, rent and unused annual allowance uprating tests.
- **The one failure in run 4** was `test_water_uprating_properties` with a Hypothesis `FailedHealthCheck` (too slow: 5 inputs in 72 s while host load1 rose to 118–147). It is not a wrong value: it passed on re-run (run 5) and in CI.

**Total:** 34 YAML cases passed. Python: 358 passed, plus 1 Hypothesis health-check failure under host load that passed on re-run and in CI.

## 5. CI

`gh pr checks 2571 -R PolicyEngine/policyengine-uk` exits 0. Every run is at head `ff13462790`:
- Test / Python 1–5 of 5, Test / YAML and Test / Result: pass.
- Aggregate impact: pass, no flagged moves on `enhanced_frs_2024_25.h5`. That is expected, since that file is unlabelled.
- Lint, Changes, Fix evidence, Documentation build, Test documentation builds, and Install + smoke-import on py3.11–3.14: pass.

`gh pr view --json mergeable` shows MERGEABLE. Main has moved 59 commits since the merge base 2f1606e99, including `uprating_indices.yaml`, but CI's aggregate run was on the merge with main.
