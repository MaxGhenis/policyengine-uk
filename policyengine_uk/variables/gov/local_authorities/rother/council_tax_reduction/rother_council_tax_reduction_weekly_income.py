from policyengine_uk.model_api import *


class rother_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rother Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Schedule 1 banded discount table. Universal Credit cases use the DWP-assessed UC award (universal_credit_pre_benefit_cap) less the Section 13.2 housing-costs element, the current council page's carer/limited-capability/disabled-child elements, and any additional Rother-scoped source-listed disregarded UC element, annualised by multiplying by 12 / 52 (Section 13.3), plus DWP-assessed UC earned and unearned income. Non-UC cases use claimant-and-partner net earnings after tax, primary Class 1 National Insurance, half pension contributions (Section 18.2) and the Section 19.1 25 pound weekly earnings disregard for genuine work, plus source-countable non-earnings income (Section 24 read with the Schedule 2 disregards — Child Benefit, Carer's Allowance, attendance allowance, DLA/PIP/AFIP, housing benefit, support component of ESA, bereavement support and the prescribed war-pension payments are excluded). Schedule 2 paragraph 4 disregards the whole of income for applicants on IS / income-based JSA / income-related ESA. Section 28 tariff income above 6,000 pounds of capital is added in both branches via rother_council_tax_reduction_weekly_tariff_income."
    definition_period = YEAR
    unit = GBP
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rother.council_tax_reduction
        weekly_earnings_disregard = ctr.earnings_disregard.amount * WEEKS_IN_YEAR
        tariff_income = benunit(
            "rother_council_tax_reduction_weekly_tariff_income", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # The formal PDF's Section 13.2 names housing costs, while Schedule 2
        # also disregards UC equivalents of ESA support components and carers'
        # benefits; the current council page names housing, disabled child,
        # limited capability for work, and carer elements.
        disregarded_uc_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_carer_element",
                "uc_disability_elements",
                "rother_council_tax_reduction_source_disregarded_uc_elements",
            ],
        )
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - disregarded_uc_elements,
        )
        uc_income = (
            benunit("uc_earned_income", period)
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
        # Schedule 2 paragraph 4 disregards the whole of income for applicants
        # on IS / income-based JSA / income-related ESA.
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        non_uc_income = where(passported, 0, non_uc_income)
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        return annual_income / WEEKS_IN_YEAR + tariff_income
