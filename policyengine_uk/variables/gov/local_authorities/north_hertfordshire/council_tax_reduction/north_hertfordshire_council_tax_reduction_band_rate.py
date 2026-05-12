from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "North Hertfordshire weekly income-band Council Tax Reduction rate"
    documentation = "Schedule 1 paragraph 1 of the 2026/27 scheme selects the entitlement percentage from an eight-row banded discount table indexed by household type (single / single + 1 / single + 2 / single + 3 children; couple / couple + 1 / couple + 2 / couple + 3 children) and claimant-and-partner weekly assessed income. Schedule 1 paragraph 4 caps the dependant count at three for the band column. Schedule 1 paragraph 7 places passported Income Support / income-related Employment and Support Allowance / income-based Jobseeker's Allowance applicants at Band 1 (100 per cent) regardless of weekly income."
    definition_period = YEAR
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_hertfordshire.council_tax_reduction
        weekly_income = benunit(
            "north_hertfordshire_council_tax_reduction_weekly_income", period
        )
        # Add a tiny epsilon so that float-precision noise from dividing annual
        # income by `WEEKS_IN_YEAR` does not move a weekly income near a band
        # boundary into the wrong band.
        weekly_income_for_band = weekly_income + 1e-9
        is_couple = benunit("is_couple", period)
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_dependants = benunit.sum(child_or_young_person)
        # Schedule 1 paragraph 4 caps the dependant count at three.
        capped_dependants = min_(
            num_dependants, ctr.means_test.maximum_counted_dependants
        )
        bands = ctr.income_band
        single_rate = select(
            [
                capped_dependants >= 3,
                capped_dependants == 2,
                capped_dependants == 1,
            ],
            [
                bands.single_three_or_more_children.calc(weekly_income_for_band),
                bands.single_two_children.calc(weekly_income_for_band),
                bands.single_one_child.calc(weekly_income_for_band),
            ],
            default=bands.single.calc(weekly_income_for_band),
        )
        couple_rate = select(
            [
                capped_dependants >= 3,
                capped_dependants == 2,
                capped_dependants == 1,
            ],
            [
                bands.couple_three_or_more_children.calc(weekly_income_for_band),
                bands.couple_two_children.calc(weekly_income_for_band),
                bands.couple_one_child.calc(weekly_income_for_band),
            ],
            default=bands.couple.calc(weekly_income_for_band),
        )
        banded_rate = where(is_couple, couple_rate, single_rate)
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(passported, ctr.maximum_support_rate, banded_rate)
