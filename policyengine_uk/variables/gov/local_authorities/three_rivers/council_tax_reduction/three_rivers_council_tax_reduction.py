from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_three_rivers_working_age,
)


class three_rivers_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Three Rivers Council Tax Reduction"
    documentation = "Three Rivers District Council operates an income-banded Council Tax Reduction scheme for working-age applicants from 1 April 2024, with annual band uprating; the 2026/27 bands take effect from 1 April 2026. The 2026/27 income band table sets discount rates of 100, 75, 50 and 25 per cent (with zero support above the Band 4 thresholds) indexed by household type (single / couple with no dependants / household with one dependant / household with two or more dependants). The dependant count is capped at two for the band column. The scheme caps eligible council tax at the Band D equivalent for the dwelling. The council's working-age scheme page excludes applicants whose capital is 8,000 pounds or more (the wording is `less than GBP 8,000`); the same 8,000 pound strict cutoff is applied to DWP-assessed Universal Credit capital for UC cases. The page lists no working-age non-dependant deduction schedule and no minimum award. Non-UC cases use claimant-and-partner net earnings after tax, primary Class 1 National Insurance and half pension contributions, with a 50 pound weekly earnings disregard for couples or lone parents and a 25 pound weekly earnings disregard for single workers; the page also disregards Carer's Allowance, Child Benefit, Disability Living Allowance, Personal Independence Payments and the Employment Support Allowance support component. Universal Credit cases take the DWP-assessed UC award less the source-listed Housing, Carer and disability elements (Limited Capacity to Work and Disabled Child, modelled here through PolicyEngine UK's uc_disability_elements aggregate), plus DWP-assessed UC earned income less the weekly earnings disregard and UC unearned income. Pension-age applicants route to the prescribed pensioner scheme; the working-age page does not describe a pension-age UC local-rule carve-out."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.threerivers.gov.uk/services/counciltax/ctrs"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.three_rivers.council_tax_reduction
        working_age = is_three_rivers_working_age(
            benunit.household("local_authority", period),
            benunit.household("country", period),
            benunit.household("council_tax_reduction_household_has_pensioner", period),
        )
        rate = benunit("three_rivers_council_tax_reduction_band_rate", period)
        liability = benunit.household(
            "three_rivers_council_tax_reduction_maximum_eligible_liability", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        # The council's wording `less than GBP 8,000` makes the boundary strict
        # at 8,000 — capital of exactly 8,000 is excluded.
        capital_eligible = capital < ctr.means_test.capital_limit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
