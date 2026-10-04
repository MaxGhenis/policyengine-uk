"""Synthetic probes for the round-2 review of policyengine-uk#2119.

Hand-built households only; no survey records. Each case prints the
benefit-unit outputs that decide the closure route.
"""

import sys

from policyengine_uk import Simulation

OUT = [
    "meets_pension_credit_age_conditions",
    "is_mixed_age_couple",
    "legacy_benefits_closed",
    "claims_uc_at_legacy_closure",
    "claims_universal_credit",
    "left_pension_route_at_legacy_closure",
    "is_uc_eligible",
    "housing_benefit_eligible",
    "is_pension_credit_eligible",
    "universal_credit",
    "housing_benefit",
    "pension_credit",
    "tax_credits",
    "working_tax_credit",
    "child_tax_credit",
    "income_support",
]


def person(year, **kw):
    return {k: {year: v} for k, v in kw.items()}


def run(name, year, people, benunit, household, reform=None, extra=()):
    members = list(people)
    situation = {
        "people": {n: person(year, **p) for n, p in people.items()},
        "benunits": {"b": {"members": members, **{k: {year: v} for k, v in benunit.items()}}},
        "households": {
            "h": {"members": members, **{k: {year: v} for k, v in household.items()}}
        },
    }
    sim = Simulation(situation=situation, reform=reform)
    print(f"\n### {name} ({year})", flush=True)
    for v in list(OUT) + list(extra):
        try:
            value = sim.calculate(v, year).tolist()
        except Exception as e:  # noqa: BLE001
            value = f"ERROR {type(e).__name__}: {e}"
        print(f"  {v} = {value}", flush=True)
    return sim


RENT = dict(rent=6_000, tenure_type="RENT_FROM_COUNCIL")
OLDER_WTC_HB = dict(age=72, is_claimant_or_partner=True, working_tax_credit_reported=2_000, housing_benefit_reported=6_000)
YOUNGER = dict(age=40, is_claimant_or_partner=True)


def protected(would_claim_uc, closure, extra_older=None, extra_bu=None):
    older = dict(OLDER_WTC_HB, **(extra_older or {}))
    bu = dict(
        has_mixed_age_couple_pension_credit_saving=True,
        would_claim_uc=would_claim_uc,
        would_claim_uc_at_legacy_closure=closure,
    )
    bu.update(extra_bu or {})
    return {"older": older, "younger": dict(YOUNGER)}, bu


cases = sys.argv[1:] or ["all"]

if "all" in cases or "r1" in cases:
    # r1 counterexample 1: protected 72/40 WTC+HB couple, closure claim.
    ppl, bu = protected(False, True)
    run("R1-A protected 72/40 WTC+HB, would_claim_uc F, closure T", 2025, ppl, bu, RENT)
    ppl, bu = protected(
        False,
        True,
        extra_older=dict(employment_income=10_000, weekly_hours=20),
        extra_bu=dict(would_claim_pc=False),
    )
    run("R1-A' same, older earns 10k/20h, would_claim_pc F", 2025, ppl, bu, RENT)
    # r1 counterexample 2: TC-continuation reform.
    run(
        "R1-B TC continuation reform: 35, 30h, 5k, WTC 3k, IS 4k",
        2026,
        {"adult": dict(age=35, weekly_hours=30, employment_income=5_000, working_tax_credit_reported=3_000, income_support_reported=4_000)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        {},
        reform={"gov.dwp.tax_credits.active": {"2026": True}},
        extra=["is_WTC_eligible", "is_CTC_eligible"],
    )
    run(
        "R1-B' TC continuation reform, lone parent + child 3",
        2026,
        {
            "adult": dict(age=35, weekly_hours=30, employment_income=5_000, working_tax_credit_reported=3_000, income_support_reported=4_000, child_tax_credit_reported=2_000),
            "child": dict(age=3),
        },
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        {},
        reform={"gov.dwp.tax_credits.active": {"2026": True}},
        extra=["is_WTC_eligible", "is_CTC_eligible"],
    )

if "all" in cases or "new" in cases:
    ppl, bu = protected(False, False)
    run("C1 protected WTC+HB couple, does not claim (F,F)", 2025, ppl, bu, RENT, extra=["has_mixed_age_couple_pension_credit_saving"])
    ppl, bu = protected(True, False)
    run("C2 protected WTC+HB couple, would_claim_uc T, closure F", 2025, ppl, bu, RENT)
    ppl, bu = protected(True, True)
    run("C3 protected WTC+HB couple, both flags T", 2025, ppl, bu, RENT)
    # Inferred saving (no explicit input): born early enough, pension-age HB.
    run(
        "C4 mixed-age WTC+HB couple, saving inferred, closure T",
        2025,
        {"older": dict(OLDER_WTC_HB), "younger": dict(YOUNGER)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
        extra=["has_mixed_age_couple_pension_credit_saving"],
    )
    # Mixed-age couple without the saving.
    for c in (True, False):
        run(
            f"C5 mixed-age couple WITHOUT saving on WTC+HB, closure {c}",
            2025,
            {"older": dict(OLDER_WTC_HB), "younger": dict(YOUNGER)},
            dict(has_mixed_age_couple_pension_credit_saving=False, would_claim_uc=False, would_claim_uc_at_legacy_closure=c),
            RENT,
        )
    run(
        "C6 mixed-age couple WITHOUT saving on CTC only + child, closure T",
        2025,
        {
            "older": dict(age=72, is_claimant_or_partner=True, child_tax_credit_reported=3_000, housing_benefit_reported=6_000),
            "younger": dict(YOUNGER),
            "child": dict(age=10, is_claimant_or_partner=False),
        },
        dict(has_mixed_age_couple_pension_credit_saving=False, would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    run(
        "C7 protected couple on CTC only + child (PC route), closure T",
        2025,
        {
            "older": dict(age=72, is_claimant_or_partner=True, child_tax_credit_reported=3_000, housing_benefit_reported=6_000),
            "younger": dict(YOUNGER),
            "child": dict(age=10, is_claimant_or_partner=False),
        },
        dict(has_mixed_age_couple_pension_credit_saving=True, would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    # Wholly pension-age families.
    for wc, c in ((False, True), (False, False), (True, False)):
        run(
            f"C8 single 70 on WTC+HB, would_claim_uc {wc}, closure {c}",
            2025,
            {"adult": dict(age=70, working_tax_credit_reported=2_000, housing_benefit_reported=6_000)},
            dict(would_claim_uc=wc, would_claim_uc_at_legacy_closure=c),
            RENT,
        )
    run(
        "C9 couple 70/72 on WTC+HB, closure T (reg 60A joint)",
        2025,
        {
            "a": dict(age=70, is_claimant_or_partner=True, working_tax_credit_reported=2_000, housing_benefit_reported=6_000),
            "b": dict(age=72, is_claimant_or_partner=True),
        },
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    run(
        "C10 single 70 on CTC only + child 12, no PC, closure T (PC route)",
        2025,
        {
            "adult": dict(age=70, is_claimant_or_partner=True, child_tax_credit_reported=3_000, housing_benefit_reported=6_000),
            "child": dict(age=12, is_claimant_or_partner=False),
        },
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    run(
        "C11 protected couple on WTC + PC reported (art 3A(1)(b))",
        2025,
        {"older": dict(OLDER_WTC_HB, pension_credit_reported=2_000), "younger": dict(YOUNGER)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    run(
        "C12 single 70 on WTC, earns 15k, rent 7.8k: claims UC at closure",
        2025,
        {"adult": dict(age=70, working_tax_credit_reported=2_000, housing_benefit_reported=6_000, employment_income=15_000, weekly_hours=25)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        dict(rent=7_800, tenure_type="RENT_FROM_COUNCIL"),
        extra=["housing_benefit_pre_benefit_cap", "uc_maximum_amount", "uc_income_reduction"],
    )
    run(
        "C12' same family declines the closure claim (comparison)",
        2025,
        {"adult": dict(age=70, working_tax_credit_reported=2_000, housing_benefit_reported=6_000, employment_income=15_000, weekly_hours=25)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=False),
        dict(rent=7_800, tenure_type="RENT_FROM_COUNCIL"),
        extra=["housing_benefit_pre_benefit_cap"],
    )
    # IS closure, 2026: wholly pension-age noise vs mixed-age.
    run(
        "C13 single 70 reporting IS (data noise), 2026",
        2026,
        {"adult": dict(age=70, income_support_reported=3_000, housing_benefit_reported=6_000)},
        dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    run(
        "C14 protected couple reporting IS + HB, 2026, closure T",
        2026,
        {"older": dict(age=73, is_claimant_or_partner=True, housing_benefit_reported=6_000), "younger": dict(age=41, is_claimant_or_partner=True, income_support_reported=3_000)},
        dict(has_mixed_age_couple_pension_credit_saving=True, would_claim_uc=False, would_claim_uc_at_legacy_closure=True),
        RENT,
    )
    # Later years: does the route stay coherent in 2026/2027?
    ppl, bu = protected(False, True)
    run("C15 protected WTC+HB couple, closure T, 2027", 2027, ppl, bu, RENT)

if "all" in cases or "nondep" in cases:
    # Semantic merge conflict with #2006: uc_non_dependants_counted reads
    # would_claim_uc, not claims_universal_credit.
    for wc, c in ((True, False), (False, True)):
        sim = Simulation(
            situation={
                "people": {
                    "head": {"age": {2025: 40}, "is_household_head": {2025: True}, "working_tax_credit_reported": {2025: 2_000}},
                    "son": {"age": {2025: 24}, "employment_income": {2025: 20_000}},
                },
                "benunits": {
                    "head_family": {"members": ["head"], "would_claim_uc": {2025: wc}, "would_claim_uc_at_legacy_closure": {2025: c}},
                    "son_family": {"members": ["son"], "would_claim_uc": {2025: False}, "would_claim_uc_at_legacy_closure": {2025: False}},
                },
                "households": {"home": {"members": ["head", "son"], "rent": {2025: 9_000}, "tenure_type": {2025: "RENT_PRIVATELY"}, "brma": {2025: "MAIDSTONE"}}},
            }
        )
        print(f"\n### N1 head 40 on WTC + non-dependant son 24 (20k): would_claim_uc {wc}, closure {c} (2025)")
        for v in [
            "legacy_benefits_closed",
            "claims_universal_credit",
            "is_uc_eligible",
            "uc_non_dependants_counted",
            "uc_non_dep_deductions",
            "LHA_allowed_bedrooms",
            "uc_housing_costs_element",
            "universal_credit",
        ]:
            print(f"  {v} = {sim.calculate(v, 2025).tolist()}", flush=True)
