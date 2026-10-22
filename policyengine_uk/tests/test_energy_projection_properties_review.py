"""Review-only property tests for PR #2571 (energy price-basis projection).

Written by the UK hub's independent reviewer; not part of the PR. Invariants:

P1  Unlabelled energy is unchanged: every projected year equals the source,
    bitwise, the basis stays None, and the source is not mutated.
P2  Projection is idempotent: re-applying apply_uprating to a projected
    dataset changes no energy amount and no basis.
P3  Path independence (no double projection): projecting to year k, saving
    the year-k child to H5, reloading and projecting again gives the same
    amounts as one projection from the original observation.
P4  Ratio identity: a labelled amount in year y equals the source amount
    times prod_{t=b+1..y} (1 + g_t) of the OBR CPI growth series (computed
    here independently of the generated index), b the declared year.
P5  Reset coherence: after reset_growthfactor_uprating, every stored energy
    amount in a later year carries the basis that year declares, no energy
    column is created, and the base year is untouched.
P6  Declaration round trip: any valid declaration survives copy and H5
    save/load (single and multi-year); invalid ones raise ValueError.
"""

import copy
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    apply_uprating,
    extend_single_year_dataset,
    reset_growthfactor_uprating,
)
from policyengine_uk.data.energy_price_basis import parse_energy_price_basis

ENERGY = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)
GROWTH = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"

SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

_PARAMETERS = None


def parameters():
    global _PARAMETERS
    if _PARAMETERS is None:
        _PARAMETERS = CountryTaxBenefitSystem().parameters
    return _PARAMETERS


amounts = st.lists(
    st.floats(min_value=0, max_value=1e5, allow_nan=False, width=32),
    min_size=1,
    max_size=4,
)
period_types = st.sampled_from(["calendar_year", "fiscal_year"])
bases = st.builds(
    lambda kind, year: {"period_type": kind, "period_value": year},
    period_types,
    st.integers(2010, 2032),
)
maybe_bases = st.one_of(st.none(), bases)


def make_dataset(values, year=2024, basis=None, columns=ENERGY):
    n = len(values)
    ids = list(range(1, n + 1))
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [40] * n,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "region": ["LONDON"] * n,
                "tenure_type": ["OWNED_OUTRIGHT"] * n,
                "council_tax": [0.0] * n,
                "rent": [0.0] * n,
                "household_weight": [1.0] * n,
                **{c: [float(v) for v in values] for c in columns},
            }
        ),
        fiscal_year=year,
        energy_price_basis=basis,
    )


def growth_ratio(source_year, target_year):
    growth = parameters().get_child(GROWTH)
    ratio = 1.0
    if target_year >= source_year:
        for t in range(source_year + 1, target_year + 1):
            ratio *= 1 + growth(f"{t}-01-01")
    else:
        for t in range(target_year + 1, source_year + 1):
            ratio /= 1 + growth(f"{t}-01-01")
    return ratio


@SETTINGS
@given(values=amounts, year=st.integers(2023, 2030))
def test_p1_unlabelled_energy_is_unchanged(values, year):
    source = make_dataset(values, year)
    before = source.household[list(ENERGY)].copy()
    projected = extend_single_year_dataset(source, parameters())
    for y in projected.years:
        assert projected[y].energy_price_basis is None
        for c in ENERGY:
            np.testing.assert_array_equal(
                projected[y].household[c].to_numpy(), before[c].to_numpy()
            )
    pd.testing.assert_frame_equal(source.household[list(ENERGY)], before)
    frozen = reset_growthfactor_uprating(projected.copy())
    for y in frozen.years:
        assert frozen[y].energy_price_basis is None
        for c in ENERGY:
            np.testing.assert_array_equal(
                frozen[y].household[c].to_numpy(), before[c].to_numpy()
            )


@SETTINGS
@given(values=amounts, year=st.integers(2023, 2030), basis=maybe_bases)
def test_p2_projection_is_idempotent(values, year, basis):
    once = extend_single_year_dataset(make_dataset(values, year, basis), parameters())
    twice = apply_uprating(once, parameters())
    thrice = apply_uprating(twice, parameters())
    for y in once.years:
        for other in (twice, thrice):
            assert other[y].energy_price_basis == once[y].energy_price_basis
            for c in ENERGY:
                np.testing.assert_array_equal(
                    other[y].household[c].to_numpy(),
                    once[y].household[c].to_numpy(),
                )


@SETTINGS
@given(
    values=amounts,
    year=st.integers(2023, 2029),
    basis=bases,
    step=st.integers(1, 3),
    data=st.data(),
)
def test_p3_reloaded_child_is_not_projected_twice(
    tmp_path_factory, values, year, basis, step, data
):
    one_shot = extend_single_year_dataset(
        make_dataset(values, year, basis), parameters()
    )
    k = min(year + step, max(one_shot.years) - 1)
    path = tmp_path_factory.mktemp("child") / "child.h5"
    one_shot[k].copy().save(path)
    loaded = UKSingleYearDataset(file_path=path)
    assert loaded.energy_price_basis == one_shot[k].energy_price_basis
    again = extend_single_year_dataset(loaded, parameters())
    for y in again.years:
        if y < k:
            continue
        for c in ENERGY:
            np.testing.assert_allclose(
                again[y].household[c].to_numpy(),
                one_shot[y].household[c].to_numpy(),
                rtol=1e-5,
                atol=1e-3,
            )


@SETTINGS
@given(values=amounts, year=st.integers(2023, 2030), basis=bases)
def test_p4_projection_matches_cpi_growth_from_the_declared_year(values, year, basis):
    projected = extend_single_year_dataset(
        make_dataset(values, year, basis), parameters()
    )
    source = np.asarray(values, dtype=np.float32).astype(float)
    for y in projected.years:
        if y == year:
            # The observation itself is never re-priced.
            expected = source
            assert projected[y].energy_price_basis == basis
        else:
            expected = source * growth_ratio(basis["period_value"], y)
            assert projected[y].energy_price_basis == {
                "period_type": "fiscal_year",
                "period_value": y,
            }
        for c in ENERGY:
            np.testing.assert_allclose(
                projected[y].household[c].to_numpy(),
                expected,
                rtol=2e-4,
                atol=1e-2,
            )


column_subsets = st.sets(st.sampled_from(ENERGY), max_size=3).map(
    lambda s: tuple(c for c in ENERGY if c in s)
)


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    base_columns=column_subsets,
    base_basis=maybe_bases,
    later=st.lists(st.tuples(column_subsets, maybe_bases), min_size=1, max_size=3),
)
def test_p5_reset_keeps_each_amount_in_step_with_its_basis(
    base_columns, base_basis, later
):
    base = make_dataset([1.0, 2.0], 2024, base_basis, base_columns)
    datasets = [base]
    originals = {}
    for offset, (columns, basis) in enumerate(later, start=1):
        # Later amounts differ from the base so a replacement is visible.
        d = make_dataset(
            [100.0 + offset, 200.0 + offset], 2024 + offset, basis, columns
        )
        datasets.append(d)
        originals[2024 + offset] = (
            columns,
            copy.deepcopy(basis),
            d.household[list(columns)].copy(),
        )
    base_before = base.household[list(base_columns)].copy()
    multi = UKMultiYearDataset(datasets=datasets)
    reset_growthfactor_uprating(multi)
    pd.testing.assert_frame_equal(
        multi[2024].household[list(base_columns)], base_before
    )
    assert multi[2024].energy_price_basis == base_basis
    for year, (columns, basis_before, values_before) in originals.items():
        current = multi[year]
        assert set(ENERGY) & set(current.household.columns) == set(columns)
        basis_after = current.energy_price_basis
        for c in columns:
            stored = current.household[c].to_numpy()
            if np.array_equal(stored, values_before[c].to_numpy()):
                carried = basis_before
            else:
                np.testing.assert_array_equal(stored, base_before[c].to_numpy())
                carried = base_basis
            assert carried == basis_after, (
                f"{year} {c}: amount at {carried}, declared {basis_after}"
            )


valid_basis = st.builds(
    lambda kind, year: {"period_type": kind, "period_value": year},
    period_types,
    st.integers(1, 9999),
)


@SETTINGS
@given(basis=valid_basis, multi=st.booleans())
def test_p6_declaration_round_trips(tmp_path_factory, basis, multi):
    dataset = make_dataset([5.0], 2024, basis)
    assert dataset.copy().energy_price_basis == basis
    path = tmp_path_factory.mktemp("rt") / "d.h5"
    if multi:
        second = make_dataset([5.0], 2025, None)
        UKMultiYearDataset(datasets=[dataset, second]).save(str(path))
        loaded = UKMultiYearDataset(str(path))
        assert loaded[2024].energy_price_basis == basis
        assert loaded[2025].energy_price_basis is None
    else:
        dataset.save(path)
        assert UKSingleYearDataset(file_path=path).energy_price_basis == basis


invalid_basis = st.one_of(
    st.builds(
        lambda kind, year: {"period_type": kind, "period_value": year},
        st.text(max_size=12).filter(
            lambda s: s not in ("calendar_year", "fiscal_year")
        ),
        st.integers(1, 9999),
    ),
    st.builds(
        lambda kind, year: {"period_type": kind, "period_value": year},
        period_types,
        st.one_of(
            st.integers(max_value=0),
            st.integers(min_value=10000),
            st.floats(allow_nan=True),
            st.booleans(),
            st.text(max_size=4),
        ),
    ),
    st.builds(
        lambda kind, year, extra: {
            "period_type": kind,
            "period_value": year,
            "source": extra,
        },
        period_types,
        st.integers(1, 9999),
        st.text(max_size=4),
    ),
    st.lists(st.integers(), max_size=2),
    st.integers(),
)


@SETTINGS
@given(declaration=invalid_basis)
def test_p6_invalid_declarations_raise_value_error(declaration):
    with pytest.raises(ValueError):
        parse_energy_price_basis(declaration)
