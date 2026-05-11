# CTR First-Pass Workflow

Use this when an agent is asked to add one Council Tax Reduction scheme before Codex review. The goal is a clean first-pass commit that preserves review history.

## Start

- Work in `/Users/maxghenis/worktrees/policyengine-uk-1534-ctr-framework` on `codex/ctr-framework`.
- Confirm `git status --short` is clean. If not clean, stop and summarize the existing changes.
- Pull with `git pull --ff-only` only when the worktree is clean.
- Read `scheme_encoding_guidance.md`, `agent_handoff.md`, and `scheme_work_queue.md`.
- Add exactly one council. Do not push.

## Source And Scope

- Use primary official sources: adopted scheme PDF, current council page, committee report, or legislation.
- If a current report says the scheme is unchanged, pair it with the carried-forward full scheme text and cite both.
- Do not implement an income-banded scheme from headline summaries alone. If the adopted thresholds are unavailable, mark it source incomplete and choose another council.
- Before coding, write a source-facts table covering scheme year, archetype, maximum support, band cap, capital boundary, taper or bands, UC income/capital, non-dependants, pension-age routing, alternative maximum or second adult rebate, protected groups, and known limitations.
- Visually verify PDF tables when `pdftotext` omits or mangles them.

## TDD And Implementation

- Add failing YAML tests first in `policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml`.
- Confirm focused tests fail before implementation.
- Keep all parameters and variables jurisdiction-scoped under the council's folder.
- Register the council in `config.py`, `simulated_council_tax_reduction_benunit.py`, `README.md`, `scheme_work_queue.md`, `agent_handoff.md`, and `changelog.d/council-tax-reduction.added.md`.
- Cover headline maximum award, capital boundary, taper or band movement, UC path if mentioned, non-dependant behavior, pension-age routing when relevant, and one source-specific edge.

## Review Traps

- Inspect definitions of "pensioner" and "person who is not a pensioner"; implement pension-age UC relevant-period and regulation 60A carve-outs when present.
- Use UC/DWP-assessed capital for UC cases when the source says so; do not fall back to household savings.
- Do not let passported income-based benefits bypass capital unless the source says the capital rule is disapplied.
- Distinguish an actual UC award from `would_claim_uc`.
- Check whether UC income means UC assessed income, the UC award, a pre-deduction award, or named UC elements.
- Check whether non-dependant deductions reduce eligible liability before the percentage or reduce the final award after.
- For protected groups, verify who counts: claimant, partner, dependants, benefit-unit members, household members, or non-dependants.
- Match source units and basis exactly: weekly, monthly, annual; gross, net, earned, total.

## Verify

- Run focused tests for the new council.
- Run one sanity test for a recently added similar scheme.
- Run ruff format and ruff check on touched Python files.
- Run an import smoke check for the new variables with `CountryTaxBenefitSystem`.
- Run `git diff --check`.
- Revert `uv.lock` churn unless genuinely needed.
- Remove `__pycache__`.

## Commit Before Codex

- Commit the first pass locally before asking Codex to review.
- Commit only the one council and required shared test/config/docs/changelog changes.
- Use commit message `Add <Council> Council Tax Reduction`.
- Do not push.

## Codex Review

- After the first-pass commit, run `/codex` review if available.
- Ask Codex to review only source fidelity, missing tests, and integration risks.
- Give Codex the source URL(s), source-facts table, files changed, tests added, known limitations, and first-pass commit hash.
- Fix actionable findings with a failing test where practical.
- If fixes are needed, commit them separately as `Fix <Council> CTR review findings`.
- Do not push.

## Final Response

Report the council, commit hash(es), source URL(s), source-facts table, tests and commands run, Codex findings/fixes, known limitations, `uv.lock` status, and final `git status --short`.
