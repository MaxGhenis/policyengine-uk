from policyengine_uk.model_api import *


class rochford_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Rochford weekly income-band CTS rate"
    documentation = "The working-age scheme page selects the entitlement percentage from a six-row, six-column table indexed by household type (single / couple x no / one / two or more children) and the claimant and partner's net weekly income. Applicants on Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance receive the maximum 75 per cent (Band 1) regardless of income band."
    definition_period = YEAR
    reference = (
        "https://www.rochford.gov.uk/local-council-tax-support-for-working-age-people"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rochford.council_tax_reduction
        weekly_income = benunit("rochford_council_tax_reduction_weekly_income", period)
        # Pad slightly so that exactly-on-the-boundary tests fall in the lower band.
        weekly_income_for_band = weekly_income + 1e-9
        is_couple = benunit("is_couple", period)
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_dependants = benunit.sum(child_or_young_person)
        bands = ctr.income_band
        single_rate = select(
            [num_dependants >= 2, num_dependants == 1],
            [
                bands.single_two_or_more_children.calc(weekly_income_for_band),
                bands.single_one_child.calc(weekly_income_for_band),
            ],
            default=bands.single_no_children.calc(weekly_income_for_band),
        )
        couple_rate = select(
            [num_dependants >= 2, num_dependants == 1],
            [
                bands.couple_two_or_more_children.calc(weekly_income_for_band),
                bands.couple_one_child.calc(weekly_income_for_band),
            ],
            default=bands.couple_no_children.calc(weekly_income_for_band),
        )
        banded_rate = where(is_couple, couple_rate, single_rate)
        # Passported income-based benefit applicants (Income Support,
        # income-related ESA or income-based JSA) receive the maximum 75 per cent
        # award regardless of their weekly net income.
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(passported, ctr.maximum_support_rate, banded_rate)
