from policyengine_uk.model_api import *


class sevenoaks_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Sevenoaks Council Tax Reduction"
    documentation = "Sevenoaks operates a Banded Discount Scheme under section 13A of the Local Government Finance Act 1992 with an 80 per cent maximum award (Schedule 1 paragraph 1). The scheme indexes a five-band discount table by household type (single / couple with no children / couple or lone parent with one child / couple or lone parent with two or more children, capped at two dependants by Schedule 1 paragraph 4) and the claimant-and-partner weekly assessed income. Schedule 1 paragraph 5 strictly excludes applicants whose capital exceeds 6,000 pounds (the boundary is strict above 6,000; capital at exactly 6,000 remains eligible), while the capital disregards disregard the whole capital of applicants on Income Support, income-based Jobseeker's Allowance or income-related Employment and Support Allowance. Schedule 1 paragraph 8 places those passported applicants at Band 1 (80 per cent). Section 39.6 cancels any award calculated at less than 1 pound per week. Pension-age applicants who are not on Universal Credit, Income Support, income-based Jobseeker's Allowance or income-related Employment and Support Allowance route to the prescribed pensioner scheme via the aggregator; pension-age applicants on those benefits stay in the local working-age banded scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.sevenoaks.gov.uk/download/downloads/id/4481/council_tax_support_local_scheme_202627.docx"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.sevenoaks.council_tax_reduction
        local_scheme = benunit(
            "sevenoaks_council_tax_reduction_is_local_scheme", period
        )
        rate = benunit("sevenoaks_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        # Section 27.2 and Schedule 1 paragraph 5: apply the 6,000 pound strict
        # cutoff to household savings for non-UC cases and to DWP-assessed UC
        # capital (Section 13.5) for UC cases. The capital disregards disregard
        # the whole capital of applicants on IS/JSA-IB/ESA-IR.
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
        passported_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        capital_eligible = (capital <= ctr.means_test.capital_limit) | (
            passported_benefit & ~has_uc_award
        )
        gross_award = liability * rate
        weekly_award = gross_award / WEEKS_IN_YEAR
        # Section 39.6: any award calculated at less than 1 pound per week is
        # cancelled.
        award_meets_minimum = weekly_award >= ctr.means_test.minimum_weekly_award
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award_meets_minimum
            * gross_award
        )
