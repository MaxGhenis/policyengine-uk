from policyengine_uk.model_api import *


class wealden_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Wealden Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Wealden working-age banded discount table. Universal Credit cases take the DWP-assessed UC standard allowance and child element only (the council's working-age scheme page states `we will take into account the Standard element and the Child element`), plus UC earned income less the 25 pound weekly disregard and UC unearned income; the housing-costs, carer, disabled-child, LCWRA and childcare elements are explicitly disregarded by the council. Non-UC cases use claimant-and-partner net earnings after tax, primary Class 1 National Insurance, half pension contributions and the 25 pound weekly earnings disregard, plus source-countable non-earnings income, less eligible childcare costs. Self-employed claimants and partners outside the startup period and exceptional circumstances are floored to national living wage times 35 hours per week, or 16 hours for lone parents. Child Benefit, Carer's Allowance, attendance allowance, DLA/PIP/AFIP, ESA support component and the listed disability premiums and war pensions are excluded from countable income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wealden.gov.uk/benefits/who-can-get-council-tax-reduction/"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wealden.council_tax_reduction
        weekly_earnings_disregard = ctr.earnings_disregard.amount * WEEKS_IN_YEAR
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # The council's working-age scheme page: "we will take into account the
        # Standard element and the Child element. We will also take into
        # account any unearned and earned income Universal Credit tell us
        # about. We will deduct GBP 25.00 from the earnings. As we will not
        # take into account the Carer element and Childcare element we will
        # not disregard Childcare costs or Carer's Allowance."
        countable_uc_award = benunit("uc_standard_allowance", period) + benunit(
            "uc_child_element", period
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
        self_employment_income = person("self_employment_income", period)
        self_employed = claimant_or_partner & (self_employment_income > 0)
        mif_exempt = person(
            "wealden_council_tax_reduction_self_employment_minimum_income_floor_exempt",
            period,
        )
        mif_applies = self_employed & ~mif_exempt
        national_living_wage = parameters(
            period
        ).gov.hmrc.minimum_wage.non_apprentice.calc(25)
        mif_hours = where(person.benunit("is_lone_parent", period), 16, 35)
        annual_self_employment_income = where(
            mif_applies,
            max_(
                self_employment_income,
                national_living_wage * mif_hours * WEEKS_IN_YEAR,
            ),
            self_employment_income,
        )
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + annual_self_employment_income
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
        childcare_expenses = benunit.sum(person("childcare_expenses", period))
        non_uc_income = max_(
            0,
            countable_earnings + other_income + benefit_income - childcare_expenses,
        )
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        return annual_income / WEEKS_IN_YEAR
