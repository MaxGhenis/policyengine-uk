"""Does no_economic_assumptions change UNLABELLED energy in an external
multi-year dataset? Run against the PR tree and against main."""

import numpy as np
import pandas as pd

from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.scenarios import no_economic_assumptions

ENERGY = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)


def year_data(year, value):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "household_weight": [1.0],
                **{c: [value] for c in ENERGY},
            }
        ),
        fiscal_year=year,
    )


source = UKMultiYearDataset(datasets=[year_data(2024, 100.0), year_data(2026, 777.0)])
default = Simulation(dataset=source.copy())
frozen = Simulation(dataset=source.copy(), scenario=no_economic_assumptions)
for c in ENERGY:
    print(
        c,
        "default 2026:",
        float(np.asarray(default.calculate(c, 2026))[0]),
        "frozen 2026:",
        float(np.asarray(frozen.calculate(c, 2026))[0]),
    )
