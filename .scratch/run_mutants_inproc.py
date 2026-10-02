"""Reviewer's mutants of branch eeb4698a8, run in ONE process (the host is too
loaded to import policyengine_uk once per mutant).

Each mutant is a clone of the branch's tax-benefit system with one rule
broken: a variable module re-executed from edited source and swapped in with
replace_variable, or a parameter updated. The repo's YAML tests (and the
reviewer's cases) run against it through policyengine_core's own YAML runner
(the OpenFiscaPlugin that `policyengine-core test` uses). The Hypothesis
tests run against it by pointing policyengine_uk.simulation's system factory
at the mutant.

Usage: python run_mutants_inproc.py <workspace> <out_dir> [mutant ...]
"""

import contextlib
import io
import os
import pathlib
import sys
import time
import traceback
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()
ONLY = sys.argv[3:]
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(W))
os.chdir(W)

t0 = time.time()
import policyengine_uk  # noqa: E402
import policyengine_uk.simulation as pe_sim  # noqa: E402
import pytest  # noqa: E402
from policyengine_core.periods import instant  # noqa: E402
from policyengine_core.tools.test_runner import OpenFiscaPlugin  # noqa: E402
from policyengine_core.variables import Variable  # noqa: E402
from policyengine_uk import CountryTaxBenefitSystem  # noqa: E402

SUMMARY = OUT / "summary.txt"


def log(msg):
    line = f"[{time.time() - t0:7.0f}s] {msg}"
    print(line, flush=True)
    with SUMMARY.open("a") as f:
        f.write(line + "\n")


log(f"imported {policyengine_uk.__file__}")
BASE = CountryTaxBenefitSystem()
log("built base system")

PKG = W / "policyengine_uk"
T = "policyengine_uk/tests/policy"
TESTS = [
    f"{T}/baseline/gov/hmrc/income_tax/charges/winter_fuel_payment_charge.yaml",
    f"{T}/baseline/gov/dwp/winter_fuel_payment/relevant_benefit_receipt.yaml",
    f"{T}/baseline/gov/social_security_scotland/pawhp.yaml",
    f"{T}/reforms/parametric/winter_fuel_allowance",
    f"{T}/reforms/parametric/winter_fuel_payment_charge",
    f"{T}/baseline/finance/benefit/family/housing_benefit/applicable_income/housing_benefit_applicable_income.yaml",
    f"{T}/baseline/finance/benefit/family/income_support/legacy_family_definitions.yaml",
    f"{T}/baseline/finance/benefit/family/universal_credit/income/uc_earned_income.yaml",
    f"{T}/baseline/gov/dwp/pension_credit/claimant_partner_income_and_carers.yaml",
    f"{T}/baseline/gov/dwp/benefit_cap.yaml",
    f"{T}/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml",
    f"{T}/baseline/gov/dwp/means_test_income_members.yaml",
    f"{T}/baseline/finance/benefit/family/legacy_award_readers/means_test_income.yaml",
    ".scratch/reviewer_tests.yaml",
]


def var_op(rel, old, new):
    return ("var", rel, old, new)


def param_op(path, start, stop, value):
    return ("param", path, start, stop, value)


IT = "variables/gov/hmrc/income_tax/income_tax.py"
CHARGE_P = "gov.hmrc.income_tax.charges.winter_fuel_payment"
RB_ALL = [
    "is_on_income_support",
    "is_on_income_based_jsa",
    "is_on_pension_credit",
    "is_on_income_related_esa",
    "is_on_universal_credit",
]
BC = 'benunit.members("income_tax_before_winter_fuel_payment_charge", period)'

MUTANTS = {
    "control": [],
    # ITA 2007 s.23: the charge is Step 7, after the Step 6 tax reductions.
    "r1_charge_offset_by_tax_reductions": [
        var_op(
            IT,
            '    adds = [\n        "income_tax_before_winter_fuel_payment_charge",\n        "winter_fuel_payment_charge",\n    ]\n',
            "    def formula(person, period, parameters):\n"
            "        p = parameters(period).gov.hmrc.income_tax\n"
            "        additions = add(person, period, p.income_tax_additions)\n"
            "        subtractions = add(person, period, p.income_tax_subtractions)\n"
            '        charge = person("winter_fuel_payment_charge", period)\n'
            "        return max_(0, additions + charge - subtractions)\n",
        )
    ],
    # FA 2026 Sch 10 para 5: from 2025-26. Mutant: from 2024-25.
    "r10_charge_in_effect_2024": [
        param_op(f"{CHARGE_P}.in_effect", "2024-01-01", "2024-12-31", True)
    ],
    # s.681I(5)(d): income-related ESA exempts.
    "r5_esa_not_relevant": [
        param_op(
            f"{CHARGE_P}.relevant_benefits",
            "2025-01-01",
            None,
            [b for b in RB_ALL if b != "is_on_income_related_esa"],
        )
    ],
    # s.681I(5)(a), (b): IS and income-based JSA exempt.
    "r6_is_and_jsa_not_relevant": [
        param_op(
            f"{CHARGE_P}.relevant_benefits",
            "2025-01-01",
            None,
            [
                b
                for b in RB_ALL
                if b not in ("is_on_income_support", "is_on_income_based_jsa")
            ],
        )
    ],
    "r4_hbai_net_income_drops_pawhp": [
        var_op(
            "variables/household/income/hbai_household_net_income.py",
            '    "winter_fuel_allowance",\n    "pawhp",\n',
            '    "winter_fuel_allowance",\n',
        )
    ],
    "r9_household_benefits_drops_pawhp": [
        var_op(
            "variables/household/income/household_benefits.py",
            '    "winter_fuel_allowance",\n    "pawhp",\n',
            '    "winter_fuel_allowance",\n',
        )
    ],
    "r11_household_tax_ignores_charge": [
        var_op(
            "variables/gov/hmrc/household_tax.py",
            '    "income_tax",\n',
            '    "income_tax_before_winter_fuel_payment_charge",\n',
        )
    ],
    "r12_gov_tax_ignores_charge": [
        var_op(
            "variables/gov/gov_tax.py",
            '    "income_tax",\n',
            '    "income_tax_before_winter_fuel_payment_charge",\n',
        )
    ],
    "r2_hb_deducts_charge": [
        var_op(
            "variables/gov/dwp/housing_benefit/applicable_income/housing_benefit_applicable_income.py",
            '            "income_tax_before_winter_fuel_payment_charge",\n',
            '            "income_tax",\n',
        )
    ],
    "r3_ctr_deducts_charge": [
        var_op(
            "variables/gov/local_authorities/council_tax_reduction/council_tax_reduction_applicable_income.py",
            '["income_tax_before_winter_fuel_payment_charge", "national_insurance"]',
            '["income_tax", "national_insurance"]',
        )
    ],
    "r8_benefit_cap_earnings_deducts_charge": [
        var_op(f, BC, 'benunit.members("income_tax", period)')
        for f in [
            "variables/gov/dwp/is_benefit_cap_exempt_earnings.py",
            "variables/gov/dwp/is_benefit_cap_exempt_health_disability.py",
            "variables/gov/dwp/is_benefit_cap_exempt_other.py",
        ]
    ],
    "r7_uc_earned_income_drops_ni": [
        var_op(
            "variables/gov/dwp/universal_credit/income/uc_earned_income.py",
            '                "national_insurance",\n',
            "",
        )
    ],
    # The author's circularity claim, for comparison with r2/r3/r8.
    "r13_pc_income_deducts_charge": [
        var_op(
            "variables/gov/dwp/pension_credit/pension_credit_income.py",
            '["income_tax_before_winter_fuel_payment_charge", "national_insurance"]',
            '["income_tax", "national_insurance"]',
        )
    ],
}

HYPOTHESIS = {
    "r1_charge_offset_by_tax_reductions": ["test_payments_match_reference"],
    "r10_charge_in_effect_2024": ["test_payments_match_reference"],
    "r5_esa_not_relevant": [
        "test_payments_match_reference",
        "test_incomes_change_only_the_charge",
    ],
    "r6_is_and_jsa_not_relevant": [
        "test_payments_match_reference",
        "test_incomes_change_only_the_charge",
    ],
}


def build(name):
    system = BASE.clone()
    for op in MUTANTS[name]:
        if op[0] == "var":
            _, rel, old, new = op
            path = PKG / rel
            src = path.read_text()
            assert src.count(old) == 1, (name, rel, src.count(old))
            src = src.replace(old, new)
            mod = f"mutant_{name}_{path.stem}"
            ns = {"__name__": mod, "__file__": str(path)}
            exec(compile(src, str(path), "exec"), ns)
            classes = [
                v
                for v in ns.values()
                if isinstance(v, type)
                and issubclass(v, Variable)
                and v.__module__ == mod
            ]
            assert classes, (name, rel)
            for cls in classes:
                system.replace_variable(cls)
        else:
            _, dotted, start, stop, value = op
            node = system.parameters
            for part in dotted.split("."):
                node = getattr(node, part)
            node.update(
                start=instant(start),
                stop=instant(stop) if stop else None,
                value=value,
            )
    system._parameters_at_instant_cache = {}
    return system


def run_yaml(name, system):
    xml = OUT / f"{name}.junit.xml"
    logf = OUT / f"{name}.yaml.log"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = pytest.main(
            [
                "--capture",
                "no",
                "--tb",
                "line",
                "-q",
                "-p",
                "no:cacheprovider",
                f"--junitxml={xml}",
                *TESTS,
            ],
            plugins=[OpenFiscaPlugin(system, {})],
        )
    logf.write_text(buf.getvalue())
    tree = ET.parse(xml)
    cases = list(tree.iter("testcase"))
    failed = []
    for c in cases:
        bad = c.find("failure")
        if bad is None:
            bad = c.find("error")
        if bad is not None:
            msg = (bad.get("message") or "").splitlines()[0][:160]
            failed.append(f"{c.get('classname', '')}::{c.get('name')} :: {msg}")
    return code, len(cases), failed


def run_hypothesis(name, system, tests):
    import importlib

    mod = importlib.import_module(
        "policyengine_uk.tests.test_winter_heating_payment_properties"
    )
    original = pe_sim.CountryTaxBenefitSystem
    pe_sim.CountryTaxBenefitSystem = lambda: system.clone()
    results = {}
    try:
        for t in tests:
            try:
                getattr(mod, t)()
                results[t] = "passed"
            except Exception as e:  # noqa: BLE001
                results[t] = f"FAILED: {type(e).__name__}: {str(e).splitlines()[0][:200] if str(e) else ''}"
    finally:
        pe_sim.CountryTaxBenefitSystem = original
    return results


CYCLE_SITUATIONS = {
    # A single pensioner over the threshold who rents: HB, CTR, PC paths.
    "pensioner_renter": {
        "people": {
            "p": {"age": {2025: 70}, "private_pension_income": {2025: 40_000}}
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {
            "h": {
                "members": ["p"],
                "country": {2025: "ENGLAND"},
                "rent": {2025: 9_000},
                "council_tax": {2025: 1_800},
            }
        },
    },
    # A mixed-age couple with earnings who rent: UC, benefit cap paths.
    "mixed_age_uc_couple": {
        "people": {
            "a": {"age": {2025: 40}, "employment_income": {2025: 9_000}},
            "b": {"age": {2025: 70}, "private_pension_income": {2025: 36_000}},
            "c": {"age": {2025: 8}},
        },
        "benunits": {"bu": {"members": ["a", "b", "c"]}},
        "households": {
            "h": {
                "members": ["a", "b", "c"],
                "country": {2025: "ENGLAND"},
                "rent": {2025: 12_000},
                "council_tax": {2025: 1_800},
            }
        },
    },
}


def cycle_check(name, system):
    from policyengine_core.simulations import SimulationBuilder

    out = {}
    for label, sit in CYCLE_SITUATIONS.items():
        try:
            sim = SimulationBuilder().build_from_entities(system, sit)
            v = {
                k: float(sim.calculate(k, 2025).sum())
                for k in [
                    "income_tax",
                    "winter_fuel_payment_charge",
                    "pension_credit",
                    "universal_credit",
                    "housing_benefit",
                    "council_tax_reduction",
                    "household_net_income",
                ]
            }
            out[label] = "ok " + ", ".join(f"{k}={x:.2f}" for k, x in v.items())
        except Exception as e:  # noqa: BLE001
            out[label] = f"{type(e).__name__}: {str(e)[:200]}"
    return out


for name in MUTANTS:
    if ONLY and name not in ONLY:
        continue
    try:
        system = build(name)
    except Exception:  # noqa: BLE001
        log(f"{name}: BUILD FAILED\n{traceback.format_exc()}")
        continue
    cyc = cycle_check(name, system)
    for label, res in cyc.items():
        log(f"{name} cycle-check {label}: {res}")
    if name == "r13_pc_income_deducts_charge":
        continue
    code, n, failed = run_yaml(name, system)
    verdict = "KILLED" if failed else "SURVIVED"
    log(f"{name}: YAML {n - len(failed)}/{n} passed, {len(failed)} failed -> {verdict} (pytest exit {code})")
    for f in failed:
        log(f"    {f}")
    if name in HYPOTHESIS:
        res = run_hypothesis(name, system, HYPOTHESIS[name])
        for t, r in res.items():
            log(f"{name} hypothesis {t}: {r}")
log("done")
