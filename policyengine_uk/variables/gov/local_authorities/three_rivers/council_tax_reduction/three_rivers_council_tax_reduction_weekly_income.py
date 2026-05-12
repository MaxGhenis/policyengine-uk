from policyengine_uk.model_api import *


class three_rivers_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Three Rivers Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Three Rivers banded discount table. Non-UC cases use claimant-and-partner net earnings after tax, primary Class 1 National Insurance and half pension contributions; the council deducts the GBP 50 weekly earnings disregard for couples or lone parents who are in work and the GBP 25 weekly earnings disregard for single workers. Source-countable non-earnings income is added; Child Benefit, Carer's Allowance, Disability Living Allowance, Personal Independence Payments are excluded from countable income. The source also names the Employment Support Allowance support component as a disregard but PolicyEngine UK does not separate the support component from the contributory ESA award, so esa_contrib is currently included in countable income (known approximation). Universal Credit cases use the DWP-assessed UC award (universal_credit_pre_benefit_cap) less the source-listed Housing, Carer and disability (LCW / Disabled Child, modelled through PolicyEngine UK's uc_disability_elements aggregate) elements, plus any further source-listed disregarded UC element supplied through the Three Rivers source input, plus DWP-assessed UC earned income less the weekly earnings disregard and UC unearned income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.threerivers.gov.uk/services/counciltax/ctrs"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.three_rivers.council_tax_reduction
        # GBP 50 per week applies to couples and lone parents; GBP 25 to singles.
        weekly_earnings_disregard = where(
            benunit("is_couple", period) | benunit("is_lone_parent", period),
            ctr.earnings_disregard.couple_or_lone_parent,
            ctr.earnings_disregard.single,
        )
        annual_earnings_disregard = weekly_earnings_disregard * WEEKS_IN_YEAR

        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # The council's working-age scheme page disregards the Carer, Disabled
        # Child, Housing and Limited Capacity to Work elements of Universal
        # Credit. PolicyEngine UK's uc_disability_elements covers LCWRA and
        # disabled-child; the source input absorbs any residual source-listed
        # disregard such as a standalone Limited Capacity for Work element.
        disregarded_uc_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_carer_element",
                "uc_disability_elements",
                "three_rivers_council_tax_reduction_source_disregarded_uc_elements",
            ],
        )
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - disregarded_uc_elements,
        )
        countable_uc_earned_income = max_(
            0,
            benunit("uc_earned_income", period) - annual_earnings_disregard,
        )
        uc_income = (
            countable_uc_award
            + countable_uc_earned_income
            + benunit("uc_unearned_income", period)
        )

        person = benunit.members
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
        # The disregard applies only to in-work claimants per the page wording.
        applied_earnings_disregard = (gross_earnings > 0) * annual_earnings_disregard
        countable_earnings = max_(0, net_earnings - applied_earnings_disregard)
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
                    "jsa_contrib",
                    "esa_contrib",
                    "incapacity_benefit",
                ],
            )
        )
        non_uc_income = countable_earnings + other_income + benefit_income
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        return annual_income / WEEKS_IN_YEAR
