from policyengine_uk.model_api import *


class wirral_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Wirral weekly income-band Council Tax Reduction rate"
    documentation = "Schedule 1 Table 1 of the 2026/27 scheme selects the entitlement percentage from a five-band table (50/40/30/20/0 per cent) indexed by household type (single / single with one dependant / single with 2+ dependants / couple / couple with one dependant / couple with 2+ dependants) and claimant-and-partner weekly assessed income. Schedule 1 caps the dependant count at 2+ for the band column. Schedule 1 paragraph 7 forces Band 1 (50 per cent) for applicants on Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance regardless of weekly income."
    definition_period = YEAR
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wirral.council_tax_reduction
        weekly_income = benunit("wirral_council_tax_reduction_weekly_income", period)
        # Add a tiny epsilon so that float-precision noise from dividing annual
        # income by `WEEKS_IN_YEAR` does not move a weekly income near a band
        # boundary into the wrong band. The published bands treat each
        # threshold as the start of the next band (e.g. `GBP 130.01` starts
        # Band 2), so this epsilon is a no-op at the exact thresholds.
        weekly_income_for_band = weekly_income + 1e-9
        is_couple = benunit("is_couple", period)
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_dependants = benunit.sum(child_or_young_person)
        capped_dependants = min_(
            num_dependants, ctr.means_test.maximum_counted_dependants
        )
        bands = ctr.income_band
        no_children_rate = where(
            is_couple,
            bands.couple.calc(weekly_income_for_band),
            bands.single.calc(weekly_income_for_band),
        )
        one_child_rate = where(
            is_couple,
            bands.couple_with_one_child.calc(weekly_income_for_band),
            bands.single_with_one_child.calc(weekly_income_for_band),
        )
        two_or_more_child_rate = where(
            is_couple,
            bands.couple_with_two_or_more_children.calc(weekly_income_for_band),
            bands.single_with_two_or_more_children.calc(weekly_income_for_band),
        )
        income_band_rate = select(
            [capped_dependants >= 2, capped_dependants == 1],
            [two_or_more_child_rate, one_child_rate],
            default=no_children_rate,
        )
        # Schedule 1 paragraph 7 forces Band 1 for passported claimants on
        # IS / income-based JSA / income-related ESA.
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(passported, ctr.maximum_support_rate, income_band_rate)
