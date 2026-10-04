"""Mutation-masking detector for the universal credit limb of the HB passport.

For every YAML case under policyengine_uk/tests/policy, find the benefit units
that the universal credit limb alone passports (is_uc_entitled with the limb in
force and no legacy benefit). For each case with such a unit, perturb the
means-test branch of each of the three passported variables (only where the
family is not passported) and record whether the case's asserted outputs move:

- with the limb on (the PR), and
- with the limb off (the parameter switched to false).

A case is MASKED for a mutation when the limb-off run detects it and the
limb-on run does not: the universal credit passport hides the means-test code
the assertion would otherwise check. Cases that supply the passported inputs,
that test a family HB-ineligible by route, or that hold any other value fixed
cannot be masked, because the perturbation does not reach their outputs either
way.

Usage: masking_detector.py <shard> <nshards> <out.json>
"""

import glob
import json
import sys
import traceback

import numpy as np
import yaml
from policyengine_core import periods
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk.model_api import where
from policyengine_uk.system import system as BASE

shard, nshards, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]

MUTATIONS = {
    "none": None,
    "disregard": ("housing_benefit_applicable_income_disregard", 13.13),
    "income": ("housing_benefit_applicable_income", 777.77),
    "capital": ("housing_benefit_assessable_capital", 50_000.0),
}


def build(limb_on, mutation):
    tbs = BASE.clone()
    if not limb_on:
        node = tbs.parameters.gov.dwp.housing_benefit.means_test.universal_credit_passport
        for child in ("great_britain", "northern_ireland"):
            getattr(node, child).update(
                period=periods.period("year:2000:60"), value=False
            )
    spec = MUTATIONS[mutation]
    if spec is not None:
        name, delta = spec
        variable = tbs.variables[name]
        for start, original in list(variable.formulas.items()):

            def wrapped(benunit, period, parameters, original=original, delta=delta):
                value = original(benunit, period, parameters)
                passport = benunit("housing_benefit_on_passporting_benefit", period)
                return value + where(passport, 0, delta)

            variable.formulas[start] = wrapped
    return tbs


SYSTEMS = {
    (limb, m): build(limb, m) for limb in (True, False) for m in MUTATIONS
}


def leaf_checks(case, sim, tbs):
    """Yield (variable, period, entity_index, expected) as the YAML runner does."""
    default_period = case.get("period")

    def expand(variable, expected, period, index):
        if isinstance(expected, dict):
            for p, v in expected.items():
                yield from expand(variable, v, p, index)
        else:
            yield variable, period, index, expected

    for key, expected in (case.get("output") or {}).items():
        if key in tbs.variables:
            yield from expand(key, expected, default_period, None)
        elif sim.populations.get(key):
            for v, val in expected.items():
                yield from expand(v, val, default_period, None)
        else:
            population = sim.get_population(plural=key)
            for instance_id, values in expected.items():
                idx = population.get_index(instance_id)
                for v, val in values.items():
                    yield from expand(v, val, default_period, idx)


def margin(case):
    a, r = case.get("absolute_error_margin"), case.get("relative_error_margin")
    if a is None and r is None:
        a = 1e-3
    return a, r


def values(case, tbs):
    builder = SimulationBuilder()
    builder.set_default_period(case["period"])
    sim = builder.build_from_dict(tbs, case.get("input") or {})
    sim.default_calculation_period = builder.default_period
    result = {}
    for variable, period, idx, expected in leaf_checks(case, sim, tbs):
        v = sim.calculate(variable, period)
        if idx is not None:
            v = v[idx]
        v = np.atleast_1d(np.asarray(v))
        if v.dtype.kind in "OUS":
            v = v.astype(str)
        else:
            v = v.astype(float)
        result[f"{variable}@{period}#{idx}"] = (v, expected)
    return sim, result


def same(a, b, case):
    if a.dtype.kind == "U" or b.dtype.kind == "U":
        return bool((a == b).all())
    abs_m, rel_m = margin(case)
    diff = np.abs(a - b)
    tol = abs_m if abs_m is not None else 0
    return bool((diff <= max(tol, 1e-6)).all())


def passes(result, case):
    try:
        return _passes(result, case)
    except Exception:
        return None  # expected value is an expression or enum name


def _passes(result, case):
    abs_m, rel_m = margin(case)
    for key, (v, expected) in result.items():
        if v.dtype.kind == "U":
            exp = np.atleast_1d(np.asarray(expected)).astype(str)
            if not (v == exp).all():
                return False
            continue
        exp = np.atleast_1d(np.asarray(expected, dtype=float))
        diff = np.abs(v - exp)
        if abs_m is not None and not (diff <= abs_m).all():
            return False
        if rel_m is not None and not (diff <= np.abs(rel_m * exp)).all():
            return False
    return True


files = sorted(glob.glob("policyengine_uk/tests/policy/**/*.yaml", recursive=True))
cases = []
for path in files:
    loaded = yaml.safe_load(open(path))
    if not isinstance(loaded, list):
        loaded = [loaded]
    for i, case in enumerate(loaded):
        if isinstance(case, dict) and case.get("output"):
            cases.append((path, i, case))
import os
if os.environ.get("ONLY"):
    only = {(f, i) for f, i in json.load(open(os.environ["ONLY"]))}
    cases = [c for c in cases if (c[0], c[1]) in only]
if os.environ.get("FILTER"):
    cases = [c for c in cases if os.environ["FILTER"] in c[0]]
cases = cases[shard::nshards]

rows, skipped, errors = [], [], []
for path, i, case in cases:
    raw = case.get("input") or {}
    if case.get("reforms") or any("." in k for k in raw):
        skipped.append(dict(file=path, index=i, name=case.get("name")))
        continue
    try:
        sim, base_on = values(case, SYSTEMS[(True, "none")])
        year = periods.period(str(case["period"])).this_year
        try:
            passport = np.asarray(
                sim.calculate("housing_benefit_on_passporting_benefit", year)
            ).astype(bool)
            legacy = np.asarray(
                sim.calculate("in_receipt_of_income_support_jsa_ib_or_esa_ir", year)
            ).astype(bool)
        except Exception as e:
            rows.append(dict(file=path, index=i, name=case.get("name"),
                             uc_only_benunits=None, passport_error=repr(e)[:200],
                             passes_head=passes(base_on, case)))
            continue
        uc_only = passport & ~legacy
        row = dict(
            file=path,
            index=i,
            name=case.get("name"),
            uc_only_benunits=int(uc_only.sum()),
            passes_head=passes(base_on, case),
        )
        if uc_only.any():
            _, base_off = values(case, SYSTEMS[(False, "none")])
            row["passes_limb_off"] = passes(base_off, case)
            row["outputs_move_with_limb"] = sorted(
                k for k in base_on if not same(base_on[k][0], base_off[k][0], case)
            )
            row["masked"] = {}
            for m in MUTATIONS:
                if m == "none":
                    continue
                _, mut_on = values(case, SYSTEMS[(True, m)])
                _, mut_off = values(case, SYSTEMS[(False, m)])
                detected_on = sorted(
                    k for k in base_on if not same(base_on[k][0], mut_on[k][0], case)
                )
                detected_off = sorted(
                    k for k in base_off if not same(base_off[k][0], mut_off[k][0], case)
                )
                row["masked"][m] = sorted(set(detected_off) - set(detected_on))
                row.setdefault("detected_on", {})[m] = detected_on
                row.setdefault("detected_off", {})[m] = detected_off
        rows.append(row)
    except Exception as e:
        errors.append(
            dict(file=path, index=i, name=case.get("name"), error=repr(e)[:400])
        )

json.dump(dict(rows=rows, skipped=skipped, errors=errors), open(out, "w"), indent=1)
print("cases", len(cases), "rows", len(rows), "skipped", len(skipped), "errors", len(errors))
