"""Where does tax_credits come from when WTC and CTC are both zero?"""
from policyengine_uk import Simulation

V = ["legacy_benefits_closed", "claims_universal_credit", "would_claim_CTC", "would_claim_WTC",
     "is_CTC_eligible", "is_WTC_eligible", "CTC_family_element", "CTC_child_element",
     "CTC_maximum_rate", "WTC_maximum_rate", "tax_credits_reduction", "child_tax_credit_pre_minimum",
     "working_tax_credit_pre_minimum", "tax_credits", "child_tax_credit", "working_tax_credit",
     "universal_credit", "council_tax_reduction"]

def run(name, year, adult, bu, reform=None):
    sit = {"people": {"adult": {k: {year: v} for k, v in adult.items()}, "child": {"age": {year: 3}}},
           "benunits": {"b": {"members": ["adult", "child"], **{k: {year: v} for k, v in bu.items()}}},
           "households": {"h": {"members": ["adult", "child"], "council_tax": {year: 1_500}}}}
    sim = Simulation(situation=sit, reform=reform)
    print(f"\n### {name} ({year})")
    for v in V:
        print(f"  {v} = {sim.calculate(v, year).tolist()}", flush=True)

A = dict(age=35, weekly_hours=30, employment_income=5_000, working_tax_credit_reported=3_000,
         income_support_reported=4_000, child_tax_credit_reported=2_000)
REFORM = {"gov.dwp.tax_credits.active": {"2026": True}}
run("T1 TC-continuation reform, closure claimant with WTC+CTC+IS", 2026, A,
    dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=True), REFORM)
run("T2 same, closure claim declined", 2026, A,
    dict(would_claim_uc=False, would_claim_uc_at_legacy_closure=False), REFORM)
run("T3 baseline 2024, ordinary UC claimant reporting CTC (pre-existing path)", 2024,
    dict(age=35, weekly_hours=30, employment_income=5_000, child_tax_credit_reported=2_000),
    dict(would_claim_uc=True))
