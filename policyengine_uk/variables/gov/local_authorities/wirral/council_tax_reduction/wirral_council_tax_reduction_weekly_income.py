from policyengine_uk.model_api import *


class wirral_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Wirral Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Wirral banded discount table. Non-UC cases use claimant-and-partner net earnings (Section 20.3: gross less income tax, primary Class 1 National Insurance, half of any occupational pension contribution and the Schedule 4 paragraph 1 earnings disregard of 20 pounds per week, with paragraph 2 confirming that the disregard applies to earnings irrespective of household and paragraph 3 confirming one disregard per application). Source-countable non-earnings income is added; the Schedule 2 income disregards (paragraphs 9, 11, 12 of DLA / PIP / AFIP / attendance allowance / war mobility supplement and paragraph 6 of IS / income-based JSA / income-related ESA whole-income) are excluded from countable income. Schedule 2 paragraph 72 applies a further 50 pound weekly disregard from income where the applicant or partner is in receipt of Personal Independence Payment, an Armed Forces Independence Payment or Disability Living Allowance; Schedule 2 paragraph 73 applies a further 50 pound weekly disregard from income for each qualifying dependant child who is in receipt of Personal Independence Payment or Disability Living Allowance. Universal Credit cases follow Section 12.2: counted income is the DWP-assessed UC award (universal_credit_pre_benefit_cap) less the Section 12.3 listed elements (Housing, Limited Capability for Work / Work-Related Activity, Disabled Child, Carer and Child Care - modelled here through PolicyEngine UK's uc_housing_costs_element, uc_carer_element, uc_disability_elements aggregate and any further source-listed component supplied via the Wirral source input), plus DWP-assessed UC earned income less the same Schedule 4 weekly earnings disregard, plus UC unearned income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wirral.council_tax_reduction
        annual_earnings_disregard = ctr.earnings_disregard.amount * WEEKS_IN_YEAR
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person

        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Section 12.3 disregards the Housing, LCW/LCWRA, Disabled Child,
        # Carer and Child Care elements. PolicyEngine UK's uc_disability_elements
        # covers LCWRA + disabled-child; standalone LCW and any future
        # source-listed component flow through the source input.
        disregarded_uc_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_carer_element",
                "uc_disability_elements",
                "uc_childcare_element",
                "wirral_council_tax_reduction_source_disregarded_uc_elements",
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
        # Schedule 4 paragraph 1: the earnings disregard applies only where
        # the applicant or partner has earnings from employment. Section 20.2
        # and Schedule 4 paragraph 3 then limit it to one disregard per
        # application, regardless of household composition.
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
        # Wirral's Schedule 2 does not list Carer's Allowance as a disregarded
        # benefit (it disregards DLA/PIP/AFIP at paragraph 9, war mobility
        # supplement at paragraph 11, attendance allowance at paragraph 12,
        # Child Benefit/Child Maintenance at paragraph 62, but not CA), and
        # Section 13.1 makes any unlisted income countable. Include
        # carers_allowance in the non-UC counted benefit income to match the
        # source.
        benefit_income = benunit("tax_credits", period) + benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "jsa_contrib",
                    "esa_contrib",
                    "incapacity_benefit",
                    "carers_allowance",
                ],
            )
        )
        non_uc_income = countable_earnings + other_income + benefit_income
        annual_income = where(has_uc_award, uc_income, non_uc_income)

        # Schedule 2 paragraph 72: further 50 pound weekly disregard from
        # income where the applicant or partner is in receipt of PIP, AFIP or
        # DLA, in addition to the paragraph 9 / 11 disregards of those
        # payments themselves.
        applicant_or_partner_disability = benunit.any(
            claimant_or_partner
            & (
                (person("pip", period) > 0)
                | (person("dla", period) > 0)
                | (person("afcs", period) > 0)
            )
        )
        annual_applicant_disregard = (
            applicant_or_partner_disability
            * ctr.disability_disregard.applicant_or_partner
            * WEEKS_IN_YEAR
        )

        # Schedule 2 paragraph 73: further 50 pound weekly disregard per
        # qualifying child where a dependant child of the applicant or
        # partner is in receipt of PIP or DLA (note paragraph 73 does NOT
        # list AFIP, unlike paragraph 72).
        qualifying_child = child_or_young_person & (
            (person("pip", period) > 0) | (person("dla", period) > 0)
        )
        number_qualifying_children = benunit.sum(qualifying_child)
        annual_child_disregard = (
            number_qualifying_children
            * ctr.disability_disregard.per_dependant_child
            * WEEKS_IN_YEAR
        )

        annual_income = max_(
            0,
            annual_income - annual_applicant_disregard - annual_child_disregard,
        )
        return annual_income / WEEKS_IN_YEAR
