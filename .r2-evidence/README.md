# Round 2 review evidence: PolicyEngine/policyengine-uk#2133 at 61da46a05

Scripts and logs behind the round 2 review. Mutant source trees were built under
`/tmp/uk2133r2/<variant>` (copies of `policyengine_uk/` with one edit each) and run
with `PYTHONPATH=<copy>` against this worktree's `.venv` (`uv run --frozen --no-sync`).

| Variant | Edit |
|---|---|
| `limb_off` | both dates in `universal_credit_passport.yaml` set to `false` |
| `no_min` | `standard = weekly_amount * WEEKS_IN_YEAR` (no `min_` cap) |
| `no_pence` | `covers_additional = net_earnings > (standard + childcare + additional_amount)` |
| `no_pence_ge` | the same with `>=` and no pence rounding |
| `no_legacy` | passport returns `on_universal_credit` only (legacy limb dropped) |
| `old_*` | the same edits on the 407acbd80 tree (prior round) |
| `paid_uc` | passport reads `universal_credit > 0` instead of `is_uc_entitled` (cycle negative control) |
| `pert_on` / `pert_off` | means-test branch perturbed (disregard +13.13, applicable income +777.77, capital +50,000 where not passported), limb on / off |
| `base_fix` | head code with the 8 changed existing YAML files restored to 2105816c8 |

Files:
- `run_yaml.py`: sharded `policyengine-core test` runner.
- `masking_detector.py`, `masking_detector_reforms.py`: per-YAML-case mutation-masking detector (limb on/off x three means-test perturbations); `mask_head_*.json`, `mask_retry_*.json`, `mask_reforms.json` (head), `mask_old_*.json` (positive control on 407acbd80 fixtures).
- `circularity.py`, `circularity_b.py`: 35 calculation orders on a capped lone parent with four children, GBP 18,000 private rent, 2025; `circularity*.json`.
- `sentinel_check.py`: the order test's capped sentinel, built with the test's own `situation()`.
- `compare_pymask.py`: per-test comparison of the Python masking runs (`pymask_*.xml`).
