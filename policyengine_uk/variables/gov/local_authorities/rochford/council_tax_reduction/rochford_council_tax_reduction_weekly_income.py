from policyengine_uk.model_api import *


class rochford_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rochford Council Tax Support assessed weekly income"
    documentation = "Weekly net income of the claimant and partner used to look up the working-age scheme bands. UC cases use the gross Universal Credit award (universal_credit_pre_benefit_cap) less the council's named UC element disregards: Housing costs, Carer's, Limited Capability for Work-Related Activity (modelled), Disabled Child element, plus a Rochford-scoped source input for any other source-listed disregarded element, plus DWP-assessed UC earned (after a 20 pound weekly disregard) and unearned income. Non-UC cases use claimant-and-partner net earnings after tax, NI, half pension contributions and the 20 pound weekly earnings disregard, plus source-countable non-earnings income."
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
        # Disabled Child element, plus any additional source-listed element
        # captured by the source input.
        person = benunit.members
        disregarded_uc_elements = (
            benunit("uc_housing_costs_element", period)
            + benunit("uc_carer_element", period)
            + benunit("uc_disability_elements", period)
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
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
                + person("statutory_sick_pay", period)
                + person("statutory_maternity_pay", period)
                + person("statutory_paternity_pay", period)
            )
        )
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        net_earnings = max_(0, gross_earnings - earnings_deductions)
        earnings_disregard = (
            (gross_earnings > 0) * ctr.means_test.earnings_disregard * WEEKS_IN_YEAR
        )
        countable_earnings = max_(0, net_earnings - earnings_disregard)
        other_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "property_income",
                    "private_pension_income",
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "maternity_allowance",
                    "miscellaneous_income",
                ],
            )
        )
        benefit_income = benunit("tax_credits", period) + benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "carers_allowance",
                    "jsa_contrib",
                    "esa_contrib",
                    "incapacity_benefit",
                ],
            )
        )
        non_uc_income = countable_earnings + other_income + benefit_income
        return where(
            has_uc_award,
            uc_income / WEEKS_IN_YEAR,
            non_uc_income / WEEKS_IN_YEAR,
        )
