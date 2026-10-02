"""Reviewer's own mutants of the winter fuel payment charge branch (eeb4698a8).

Usage: python mutate_review.py <src_worktree> <mutant>  -> .scratch/mut/<mutant>/policyengine_uk
None of these is in probes/mutate.py.
"""
import pathlib
import shutil
import sys

W = pathlib.Path(sys.argv[1])
name = sys.argv[2]
dest = pathlib.Path(__file__).parent / "mut" / name
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(
    W / "policyengine_uk",
    dest / "policyengine_uk",
    ignore=shutil.ignore_patterns("__pycache__"),
)


def sub(rel, old, new):
    p = dest / "policyengine_uk" / rel
    s = p.read_text()
    assert s.count(old) == 1, (rel, old, s.count(old))
    p.write_text(s.replace(old, new))


IT = "variables/gov/hmrc/income_tax/income_tax.py"
RB = "parameters/gov/hmrc/income_tax/charges/winter_fuel_payment/relevant_benefits.yaml"

if name == "control":
    pass
elif name == "r1_charge_offset_by_tax_reductions":
    # ITA 2007 s.23: the charge is Step 7, after Step 6 tax reductions.
    # Mutant adds it before the reductions, so reductions can absorb it.
    sub(
        IT,
        '    adds = [\n        "income_tax_before_winter_fuel_payment_charge",\n        "winter_fuel_payment_charge",\n    ]\n',
        "    def formula(person, period, parameters):\n"
        "        p = parameters(period).gov.hmrc.income_tax\n"
        "        additions = add(person, period, p.income_tax_additions)\n"
        "        subtractions = add(person, period, p.income_tax_subtractions)\n"
        '        charge = person("winter_fuel_payment_charge", period)\n'
        "        return max_(0, additions + charge - subtractions)\n",
    )
elif name == "r2_hb_deducts_charge":
    sub(
        "variables/gov/dwp/housing_benefit/applicable_income/housing_benefit_applicable_income.py",
        '            "income_tax_before_winter_fuel_payment_charge",\n',
        '            "income_tax",\n',
    )
elif name == "r3_ctr_deducts_charge":
    sub(
        "variables/gov/local_authorities/council_tax_reduction/council_tax_reduction_applicable_income.py",
        '["income_tax_before_winter_fuel_payment_charge", "national_insurance"]',
        '["income_tax", "national_insurance"]',
    )
elif name == "r4_hbai_net_income_drops_pawhp":
    sub(
        "variables/household/income/hbai_household_net_income.py",
        '    "winter_fuel_allowance",\n    "pawhp",\n',
        '    "winter_fuel_allowance",\n',
    )
elif name == "r5_esa_not_relevant":
    sub(RB, "      - is_on_income_related_esa\n", "")
elif name == "r6_is_and_jsa_not_relevant":
    sub(RB, "      - is_on_income_support\n      - is_on_income_based_jsa\n", "")
elif name == "r7_uc_earned_income_drops_ni":
    sub(
        "variables/gov/dwp/universal_credit/income/uc_earned_income.py",
        '                "national_insurance",\n',
        "",
    )
elif name == "r8_benefit_cap_earnings_deducts_charge":
    for f in [
        "variables/gov/dwp/is_benefit_cap_exempt_earnings.py",
        "variables/gov/dwp/is_benefit_cap_exempt_health_disability.py",
        "variables/gov/dwp/is_benefit_cap_exempt_other.py",
    ]:
        sub(
            f,
            'benunit.members("income_tax_before_winter_fuel_payment_charge", period)',
            'benunit.members("income_tax", period)',
        )
elif name == "r9_household_benefits_drops_pawhp":
    sub(
        "variables/household/income/household_benefits.py",
        '    "winter_fuel_allowance",\n    "pawhp",\n',
        '    "winter_fuel_allowance",\n',
    )
elif name == "r10_charge_in_effect_2024":
    # FA 2026 Sch 10 para 5: from 2025-26 only. Mutant starts it a year early.
    sub(
        "parameters/gov/hmrc/income_tax/charges/winter_fuel_payment/in_effect.yaml",
        "  2025-01-01:\n    value: true",
        "  2024-01-01:\n    value: true",
    )
elif name == "r11_household_tax_ignores_charge":
    sub(
        "variables/gov/hmrc/household_tax.py",
        '    "income_tax",\n',
        '    "income_tax_before_winter_fuel_payment_charge",\n',
    )
elif name == "r12_gov_tax_ignores_charge":
    sub(
        "variables/gov/gov_tax.py",
        '    "income_tax",\n',
        '    "income_tax_before_winter_fuel_payment_charge",\n',
    )
else:
    raise SystemExit(f"unknown mutant {name}")
print("made", dest)
