from policyengine_uk.model_api import *


class three_rivers_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Three Rivers weekly income-band Council Tax Reduction rate"
    documentation = "The 2026/27 income band table selects the entitlement percentage from a five-band table indexed by household type (single / couple with no dependants / household with one dependant / household with two or more dependants) and claimant-and-partner weekly assessed income. The dependant count is capped at two for the band column."
    definition_period = YEAR
    reference = "https://www.threerivers.gov.uk/services/counciltax/ctrs"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.three_rivers.council_tax_reduction
        weekly_income = benunit(
            "three_rivers_council_tax_reduction_weekly_income", period
        )
        # Add a tiny epsilon so that float-precision noise from dividing annual
        # income by `WEEKS_IN_YEAR` does not move a weekly income near a band
        # boundary into the wrong band. The published bands treat each
        # threshold as the start of the next band (e.g. `GBP 116.83` starts
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
        one_child_rate = bands.with_one_child.calc(weekly_income_for_band)
        two_or_more_child_rate = bands.with_two_or_more_children.calc(
            weekly_income_for_band
        )
        return select(
            [capped_dependants >= 2, capped_dependants == 1],
            [two_or_more_child_rate, one_child_rate],
            default=no_children_rate,
        )
