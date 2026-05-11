from policyengine_uk.model_api import *


class rochford_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Rochford Council Tax Support"
    documentation = "Rochford operates a Banded Discount Scheme with a 75 per cent maximum (the working-age scheme page states that working-age applicants must pay at least 25 per cent of their Council Tax charge). The scheme uses a six-row, six-column table indexed by household type (single / couple x no / one / two or more children) and weekly net income. Capital strictly above 6,000 pounds excludes the applicant; applicants on Income Support, income-based JSA or income-related ESA are placed at Band 1 (75 per cent). The working-age scheme has no Band cap and no non-dependant deductions; pension-age applicants follow the prescribed pensioner scheme except where the scheme treats a pension-age Universal Credit case as a person who is not a pensioner."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.rochford.gov.uk/local-council-tax-support-for-working-age-people"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rochford.council_tax_reduction
        local_scheme = benunit("rochford_council_tax_reduction_is_local_scheme", period)
        rate = benunit("rochford_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        # The working-age scheme page applies the 6,000 pound strict cutoff to
        # household savings for non-UC cases, and to DWP-assessed UC capital for
        # UC cases.
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
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
