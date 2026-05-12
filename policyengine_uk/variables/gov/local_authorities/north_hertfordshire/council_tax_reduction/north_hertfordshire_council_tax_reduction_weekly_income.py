from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "North Hertfordshire Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Schedule 1 banded discount table. Non-UC cases use claimant-and-partner net earnings after income tax, primary Class 1 National Insurance, half occupational pension contributions and the Section 20.2 50 pound weekly earnings disregard (irrespective of household, one per claim), plus source-countable non-earnings income. Schedule 2 disregards Carer's Allowance (paragraph 67), Child Benefit (paragraph 63), DLA/PIP/AFIP (paragraph 9), attendance allowance (paragraph 12), the ESA support component (paragraph 68) and the prescribed disability and war-pension benefits. PolicyEngine UK does not separate the ESA support component from the contributory ESA award, so esa_contrib is currently included in countable income (known approximation). Universal Credit cases use the DWP-assessed UC award (universal_credit_pre_benefit_cap) less the housing-costs element (and any further North Hertfordshire-scoped source-listed disregarded UC element supplied through the source input), plus DWP-assessed UC earned income less the weekly earnings disregard and UC unearned income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_hertfordshire.council_tax_reduction
        weekly_earnings_disregard = ctr.earnings_disregard.amount * WEEKS_IN_YEAR

        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        disregarded_uc_elements = benunit("uc_housing_costs_element", period) + benunit(
            "north_hertfordshire_council_tax_reduction_source_disregarded_uc_elements",
            period,
        )
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - disregarded_uc_elements,
        )
        countable_uc_earned_income = max_(
            0, benunit("uc_earned_income", period) - weekly_earnings_disregard
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
        applied_earnings_disregard = (gross_earnings > 0) * weekly_earnings_disregard
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
        # Schedule 2 paragraph 6 disregards the whole of income for applicants
        # on IS / income-based JSA / income-related ESA; Schedule 1 paragraph 7
        # also separately routes such applicants to Band 1 in band_rate.
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        non_uc_income = where(passported, 0, non_uc_income)
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        return annual_income / WEEKS_IN_YEAR
