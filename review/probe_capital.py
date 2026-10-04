"""A pension-route closure claimant refused UC on capital keeps neither PC nor HB."""
from policyengine_uk import Simulation

V = ["legacy_benefits_closed", "claims_universal_credit", "left_pension_route_at_legacy_closure",
     "uc_assessable_capital", "is_uc_eligible", "universal_credit", "housing_benefit_eligible",
     "housing_benefit", "is_pension_credit_eligible", "pension_credit"]
for closure in (True, False):
    sit = {"people": {"adult": {"age": {2025: 70}, "working_tax_credit_reported": {2025: 2_000},
                                "housing_benefit_reported": {2025: 6_000}}},
           "benunits": {"b": {"members": ["adult"], "would_claim_uc": {2025: False},
                              "would_claim_uc_at_legacy_closure": {2025: closure}}},
           "households": {"h": {"members": ["adult"], "rent": {2025: 6_000},
                                "tenure_type": {2025: "RENT_FROM_COUNCIL"}, "savings": {2025: 20_000}}}}
    sim = Simulation(situation=sit)
    print(f"\n### K1 single 70 on WTC+HB, savings 20k, closure {closure} (2025)")
    for v in V:
        print(f"  {v} = {sim.calculate(v, 2025).tolist()}", flush=True)
