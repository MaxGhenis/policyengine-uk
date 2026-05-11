from policyengine_uk.model_api import *


class wealden_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Wealden weekly income-band Council Tax Reduction rate"
    documentation = "The council's working-age scheme page selects the entitlement percentage from a four-row banded discount table indexed by household type (single / couple with no children / family with one child / family with two or more children) and claimant-and-partner weekly assessed income. The dependant count is capped at two for the band column."
    definition_period = YEAR
    reference = "https://www.wealden.gov.uk/benefits/who-can-get-council-tax-reduction/"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wealden.council_tax_reduction
        weekly_income = benunit("wealden_council_tax_reduction_weekly_income", period)
        # Pad slightly so that exactly-on-the-boundary tests fall in the lower band.
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
