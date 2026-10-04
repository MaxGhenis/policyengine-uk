"""Values for the order test's capped sentinel, built with the test's own
situation() so the inputs are exactly the test's."""
import json, sys
import numpy as np
sys.path.insert(0, "policyengine_uk/tests")
import test_housing_benefit_universal_credit_passport_properties as t
from policyengine_uk import Simulation

sim = Simulation(situation=t.situation([t.CAPPED_ON_UNIVERSAL_CREDIT]))
names = [
    "region", "would_claim_uc", "is_uc_entitled", "housing_benefit_on_passporting_benefit",
    "universal_credit_pre_benefit_cap", "uc_housing_costs_element", "housing_benefit_entitlement",
    "housing_benefit_pre_benefit_cap", "benefit_cap", "benefit_cap_reduction",
    "is_benefit_cap_exempt", "housing_benefit", "universal_credit", "child_benefit",
    "household_net_income",
]
out = {}
for n in names:
    try:
        v = sim.calculate(n, t.YEAR)
        v = v.decode_to_str() if hasattr(v, "decode_to_str") else v
        out[n] = np.asarray(v).tolist()
    except Exception as e:
        out[n] = repr(e)[:120]
print(json.dumps(out, indent=1))
