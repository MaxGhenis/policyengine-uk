from policyengine_uk.model_api import *


class rochford_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rochford Council Tax Support assessed weekly income"
    documentation = "Weekly net income of the claimant and partner used to look up the working-age scheme bands. UC cases use the gross Universal Credit award (universal_credit_pre_benefit_cap) less the council's named UC element disregards: Housing costs, Carer's, Limited Capability for Work-Related Activity (modelled), Disabled Child element (per-child, summed), plus a Rochford-scoped source input for any other source-listed disregarded element, plus DWP-assessed UC earned (after a 20 pound weekly disregard) and unearned income. Non-UC cases use the prescribed Schedule disregards via council_tax_reduction_applicable_income."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.rochford.gov.uk/local-council-tax-support-for-working-age-people"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rochford.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Named UC element disregards from the working-age scheme page:
        # Housing costs, Carer's, Limited Capability for Work-Related Activity,
        # Disabled Child element (sum per-child to benunit level), plus any
        # additional source-listed element captured by the source input.
        person = benunit.members
        disabled_child_element_total = benunit.sum(
            person("uc_individual_disabled_child_element", period)
        )
        disregarded_uc_elements = (
            benunit("uc_housing_costs_element", period)
            + benunit("uc_carer_element", period)
            + benunit("uc_LCWRA_element", period)
            + disabled_child_element_total
            + benunit(
                "rochford_council_tax_reduction_source_disregarded_uc_elements", period
            )
        )
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - disregarded_uc_elements,
        )
        weekly_earnings_disregard = ctr.means_test.earnings_disregard * WEEKS_IN_YEAR
        uc_earned_income = benunit("uc_earned_income", period)
        countable_uc_earned_income = max_(
            0, uc_earned_income - weekly_earnings_disregard
        )
        uc_income = (
            countable_uc_earned_income
            + benunit("uc_unearned_income", period)
            + countable_uc_award
        )
        return where(
            has_uc_award,
            uc_income / WEEKS_IN_YEAR,
            benunit("council_tax_reduction_applicable_income", period) / WEEKS_IN_YEAR,
        )
