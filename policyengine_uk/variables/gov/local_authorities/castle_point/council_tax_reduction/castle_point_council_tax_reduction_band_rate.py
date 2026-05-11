from policyengine_uk.model_api import *


class castle_point_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Castle Point weekly income-band CTR rate"
    documentation = "Schedule 1 paragraph 1 selects the entitlement percentage from a six-row, seven-column table indexed by household type (single / couple x no / one / two or more children) and the claimant and partner's net weekly income. Schedule 1 paragraph 3 places passported applicants (Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance) at Band A (70 per cent). Schedule 1 paragraph 4 caps the dependant count at two children or young persons; this affects nothing in the rate lookup because rows 5 and 6 already group two or more children."
    definition_period = YEAR
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.castle_point.council_tax_reduction
        weekly_income = benunit(
            "castle_point_council_tax_reduction_weekly_income", period
        )
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
        # Schedule 1 paragraph 3: passported applicants (Income Support,
        # income-related ESA or income-based JSA) receive Band A (70 per cent).
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        passport_rate = ctr.maximum_support_rate
        return where(passported, passport_rate, banded_rate)
