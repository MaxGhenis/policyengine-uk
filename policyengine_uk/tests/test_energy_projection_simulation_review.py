"""Review-only simulation checks for PR #2571 (not part of the PR).

S1  A Simulation built from a labelled single-year dataset serves
    source * I[y] / I[b] in every year 2024-2036: dataset projection through
    2032, then Core's variable-level CPI uprating, never both.
S2  filter_dataset of a projected year, rebuilt as a Simulation, serves the
    same later-year amounts as the original Simulation (no second ratio).
S3  Saving the loaded multi-year dataset and rebuilding from the file
    serves the same amounts (multi-year files are not re-projected).
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.filter_dataset import filter_dataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

ENERGY = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)
CPI = "gov.economic_assumptions.indices.obr.consumer_price_index"
SOURCE = np.array([1000.0, 0.0, 250.0])


def dataset(basis):
    ids = [1, 2, 3]
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [40, 50, 60],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "region": ["LONDON", "WALES", "SCOTLAND"],
                "tenure_type": ["OWNED_OUTRIGHT"] * 3,
                "council_tax": [0.0] * 3,
                "rent": [0.0] * 3,
                "household_weight": [1.0] * 3,
                **{c: SOURCE.copy() for c in ENERGY},
            }
        ),
        fiscal_year=2024,
        energy_price_basis=basis,
    )


def index(year):
    parameter = CountryTaxBenefitSystem().parameters.get_child(CPI)
    return parameter(f"{year}-01-01")


@pytest.mark.parametrize("kind", ["calendar_year", "fiscal_year"])
def test_s1_simulation_projects_once_through_and_past_the_horizon(kind):
    basis = {"period_type": kind, "period_value": 2024}
    simulation = Simulation(dataset=dataset(basis))
    base = index(2024)
    for year in range(2024, 2037):
        expected = SOURCE * index(year) / base
        for c in ENERGY:
            np.testing.assert_allclose(
                np.asarray(simulation.calculate(c, year)), expected, rtol=1e-5
            )


def test_s1_unlabelled_is_flat_to_2032_then_core_cpi_as_before():
    simulation = Simulation(dataset=dataset(None))
    for year in range(2024, 2033):
        for c in ENERGY:
            np.testing.assert_array_equal(
                np.asarray(simulation.calculate(c, year)), SOURCE
            )
    # Past the dataset horizon Core uprates the last stored year by the
    # variable's own CPI index (pre-existing behaviour, unchanged here).
    np.testing.assert_allclose(
        np.asarray(simulation.calculate(ENERGY[0], 2034)),
        SOURCE * index(2034) / index(2032),
        rtol=1e-5,
    )


def test_s2_filtered_household_is_not_projected_twice():
    basis = {"period_type": "calendar_year", "period_value": 2024}
    simulation = Simulation(dataset=dataset(basis))
    filtered = filter_dataset(simulation, household_id=1, year=2026)
    assert filtered.energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": 2026,
    }
    rebuilt = Simulation(dataset=filtered)
    for year in (2026, 2027, 2030, 2032, 2034):
        for c in ENERGY:
            np.testing.assert_allclose(
                np.asarray(rebuilt.calculate(c, year)),
                np.asarray(simulation.calculate(c, year))[:1],
                rtol=1e-5,
            )


def test_s3_saved_multi_year_dataset_is_not_reprojected(tmp_path):
    basis = {"period_type": "fiscal_year", "period_value": 2024}
    simulation = Simulation(dataset=dataset(basis))
    path = tmp_path / "multi.h5"
    assert isinstance(simulation.dataset, UKMultiYearDataset)
    simulation.dataset.save(str(path))
    rebuilt = Simulation(dataset=str(path))
    for year in (2024, 2026, 2029, 2032, 2035):
        for c in ENERGY:
            np.testing.assert_allclose(
                np.asarray(rebuilt.calculate(c, year)),
                np.asarray(simulation.calculate(c, year)),
                rtol=1e-6,
            )
