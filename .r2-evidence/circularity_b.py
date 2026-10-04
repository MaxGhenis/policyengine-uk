"""Circularity check for the universal credit limb of the HB passport.

A capped family on both benefits: a lone parent aged 30 with four children,
£18,000 private rent in England, 2025-26, housing_benefit_eligible supplied
(standing in for specified or temporary accommodation), claiming Universal
Credit. Computes housing_benefit, universal_credit, benefit_cap_reduction and
household_net_income in every order of those four (24 orders), plus orders
that start from the passport and its inputs, in fresh simulations, and
reports any exception (CycleError or otherwise) and any disagreement.
"""

import itertools
import json
import sys

import numpy as np

from policyengine_uk import Simulation

YEAR = 2025
TARGETS = [
    "housing_benefit",
    "universal_credit",
    "benefit_cap_reduction",
    "household_net_income",
]
REPORT = TARGETS + [
    "housing_benefit_on_passporting_benefit",
    "is_uc_entitled",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_entitlement",
    "housing_benefit_pre_benefit_cap",
    "benefit_cap",
    "uc_housing_costs_element",
]
EXTRA_FIRSTS = [
    "housing_benefit_on_passporting_benefit",
    "is_uc_entitled",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_eligible",
    "housing_benefit_pre_benefit_cap",
    "benefit_cap",
    "hbai_household_net_income",
]


def situation(earnings, uc_housing_zero, savings):
    members = ["parent"] + [f"child{i}" for i in range(4)]
    benunit = {
        "members": members,
        "housing_benefit_eligible": {YEAR: True},
        "would_claim_uc": {YEAR: True},
    }
    if uc_housing_zero:
        # HB alongside UC is for rent the UC housing costs element excludes.
        benunit["uc_housing_costs_element"] = {YEAR: 0.0}
    return {
        "people": {
            "parent": {
                "age": {YEAR: 30},
                "employment_income": {YEAR: earnings},
                "housing_benefit_reported": {YEAR: 1.0},
            },
            **{f"child{i}": {"age": {YEAR: 1 + 2 * i}} for i in range(4)},
        },
        "benunits": {"bu": benunit},
        "households": {
            "hh": {
                "members": members,
                "country": {YEAR: "ENGLAND"},
                "region": {YEAR: "NORTH_WEST"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: 18_000.0},
                "savings": {YEAR: savings},
            }
        },
    }


def run(order, **kwargs):
    sim = Simulation(situation=situation(**kwargs))
    try:
        for variable in order:
            sim.calculate(variable, YEAR)
        return {v: float(np.asarray(sim.calculate(v, YEAR))[0]) for v in REPORT}, None
    except Exception as e:  # report CycleError or anything else
        return None, f"{type(e).__module__}.{type(e).__name__}: {str(e)[:300]}"


orders = [list(p) for p in itertools.permutations(TARGETS)]
orders += [[first] + TARGETS for first in EXTRA_FIRSTS]
orders += [list(reversed(TARGETS)) + ["housing_benefit_on_passporting_benefit"]]

out = {}
for label, kwargs in {
    "earnings_3000_uc_housing_zero": dict(
        earnings=3_000.0, uc_housing_zero=True, savings=0.0
    ),
    "earnings_3000_uc_housing_zero_savings_12000": dict(
        earnings=3_000.0, uc_housing_zero=True, savings=12_000.0
    ),
}.items():
    results, errors = [], []
    for order in orders:
        values, error = run(order, **kwargs)
        if error:
            errors.append(dict(order=order, error=error))
        else:
            results.append((order, values))
    reference = results[0][1] if results else None
    disagreements = [
        dict(order=o, variable=k, value=v[k], reference=reference[k])
        for o, v in results
        for k in REPORT
        if abs(v[k] - reference[k]) > 0.01
    ]
    cap_taken = None
    if reference:
        cap_taken = (
            reference["housing_benefit_pre_benefit_cap"]
            - reference["housing_benefit"]
            + reference["universal_credit_pre_benefit_cap"]
            - reference["universal_credit"]
        )
    out[label] = dict(
        orders_run=len(orders),
        orders_ok=len(results),
        errors=errors,
        disagreements=disagreements,
        values=reference,
        cap_subtracted_from_hb_and_uc=cap_taken,
    )
    print(
        label,
        "orders",
        len(orders),
        "ok",
        len(results),
        "errors",
        len(errors),
        "disagreements",
        len(disagreements),
    )
    print(json.dumps(reference, indent=1))
    print("cap subtracted in total:", cap_taken)
json.dump(out, open(sys.argv[1], "w"), indent=1)
