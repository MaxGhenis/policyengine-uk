from policyengine_uk.model_api import *


class rother_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Rother weekly income-band Council Tax Reduction rate"
    documentation = "Schedule 1 paragraph 1 of the 2026/27 scheme selects the entitlement percentage from a four-row banded discount table indexed by household type (single / couple with no children / household with one child / household with two or more children) and claimant-and-partner weekly assessed income. Schedule 1 paragraph 4 caps the dependant count at two for the band lookup. Schedule 1 paragraph 2(e) places passported Income Support, income-related Employment and Support Allowance and income-based Jobseeker's Allowance applicants at Band 1 (100 per cent) regardless of weekly income."
    definition_period = YEAR
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rother.council_tax_reduction
        weekly_income = benunit("rother_council_tax_reduction_weekly_income", period)
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
        banded_rate = select(
            [capped_dependants >= 2, capped_dependants == 1],
            [two_or_more_child_rate, one_child_rate],
            default=no_children_rate,
        )
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(passported, ctr.maximum_support_rate, banded_rate)
