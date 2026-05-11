from policyengine_uk.model_api import *


class sevenoaks_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Sevenoaks Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Schedule 1 banded discount table. Universal Credit cases use the gross UC award (universal_credit_pre_benefit_cap) less the UC housing-costs element (Section 13.3) plus DWP-assessed UC earned income (after the Section 19.2 25 pound weekly disregard) and UC unearned income, annualised by multiplying by 12 / 52 (Section 13.4). Non-UC cases use claimant-and-partner net earnings after tax, National Insurance, half pension contributions and the 25 pound weekly earnings disregard (Section 19.2 and Section 18), plus source-countable non-earnings income (Section 24 read with the Schedule 2 disregards — Child Benefit, Carer's Allowance, attendance allowance, DLA/PIP/ADP/AFIP, housing benefit and bereavement support are excluded)."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.sevenoaks.gov.uk/download/downloads/id/4481/council_tax_support_local_scheme_202627.docx"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.sevenoaks.council_tax_reduction
        weekly_earnings_disregard = ctr.means_test.earnings_disregard * WEEKS_IN_YEAR
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Section 13.3 names only the UC housing-costs element as the adjustment
        # the authority makes to DWP-assessed UC income.
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - benunit("uc_housing_costs_element", period),
        )
        uc_earned_income = benunit("uc_earned_income", period)
        countable_uc_earned_income = max_(
            0, uc_earned_income - weekly_earnings_disregard
        )
        uc_income = (
            countable_uc_earned_income
            + benunit("uc_unearned_income", period)
            + countable_uc_award
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
        earnings_disregard = (gross_earnings > 0) * weekly_earnings_disregard
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
