# Fix the Sol review's findings on PR #2092 (Pension Credit and pension-age HB projections)

You are a build job for the UK hub (Claude session 8e19f9d5). PR #2092 is Anthony Volk's (`anth-volk`), branch `feature/pension-credit-2025-rates`. The hub's reconcile build merged main into it as **9b0d406723d172e8a07c0ef42d57fd010251b977**. Confirm with `gh pr view 2092 -R PolicyEngine/policyengine-uk --json headRefName,headRefOid`. If the head has moved, stop and report it. Add your commits on top of that head: no rebase, no force-push, and keep Anthony's authorship of his commits.

The hub's independent review (GPT-6.1 Sol) of 9b0d40672 asked for changes. **Its full text is in `REVIEW-sol-r1.md` in this folder; read all of it first.** It found:
- **P2-1:** maximum Savings Credit reforms lose their forecast effects, in `create_savings_credit_threshold.py` (around :302) and `create_pension_age_allowances.py` (around :229).
- **P2-2:** the newly linked Pension Credit notebook isn't published (`myst.yml`).
- **P3-1 and P3-2:** two stale lines in the PR body.

## What to do

1. **P2-1.** Make a reform to `savings_credit.maximum` (any relationship, and both base-year and future anchors) reach both dependent forecasts: the Savings Credit threshold and the higher pension-age HB allowances. Keep the unreformed guarantee and phase-in context, and keep the existing own-base reform fallback.
   - The review's code is a proposal, not a validated patch. Use it only if it's right, and say what you changed from it.
   - First add the review's zero-maximum test (in `test_pension_age_projection_invariants.py`) and watch it fail at 9b0d40672. Then make it pass.
   - Add cases for a future maximum anchor, for a maximum reform combined with an own-base threshold or allowance reform, and for both public reform interfaces (a `Scenario`/reform dict and a structural reform), as the review lists.
   - Extend the combined Hypothesis property so it draws maximum paths too.
   - All four of the PR body's invariants must still hold. With no reform, the outputs must not move: the differential test against main's builders must still pass.
2. **P2-2.** Register `docs/book/programs/gov/dwp/pension-credit.ipynb` in `myst.yml`'s Programmes block, as the review gives it. Build the docs if the gate allows. Check that the Pension Credit page and the State Pension page's link to `pension-credit.ipynb#uprating` are both there. If the docs build can't run locally, say so: docs CI is then the evidence, and the hub will read its page list.
3. **P3-1 and P3-2 (PR body).** Replace the stale evidence paragraphs and the `axiom:` line. Use the review's wording, updated for what you actually ran. Don't claim an encoding, a parity result or tests you didn't run.
4. **Tests,** gated as below:
   - the new and changed projection tests;
   - `test_pension_age_projection_invariants.py`, `test_pension_credit_uprating.py`, `test_housing_benefit_protected_allowance_uprating.py`, `test_pension_credit_guarantee_reform_projections.py`, `test_savings_credit_threshold_projection.py` and `test_process_time_reforms.py`;
   - the Pension Credit and Housing Benefit YAML directories.

   Gate: `python3 ~/reviews/fleet-ops/tools/reservation.py allowed uk-hub` exits 0, load1 is at most 100, free disk is at least 55 GB decimal, and `~/reviews/uk-hub/DISK_HOLD` is absent. Run with `-n 2`, in the foreground. Cap any Hypothesis-heavy or mutation run with `python3 ~/reviews/disk-sustainable-2026-10-09/tools/run_capped.py --rss-gb 2 -- <cmd>`. If the gate stays closed, list what you couldn't run; CI is then the evidence.
5. **Push once,** after `uvx ruff format --check .` and the fix-evidence checker pass. Add a changelog fragment only if the fix changes behaviour that `2092.fixed.md` doesn't already describe.
6. **Post a hand-off comment** on #2092 with:
   - the new head;
   - each finding and how it was fixed, with file:line;
   - what you took from the review's proposal and what you changed;
   - the tests, with counts, and what didn't run;
   - a worked example: the zero-maximum case's 2027 threshold and higher HB allowance before and after, against the review's figures.

   Don't mark the PR ready and don't merge. The hub dispatches the re-review.

Vahid's CHANGES_REQUESTED (8 Oct) and the 13 Oct follow-up stay open. Don't dismiss them; the hub handles that after the re-review.
