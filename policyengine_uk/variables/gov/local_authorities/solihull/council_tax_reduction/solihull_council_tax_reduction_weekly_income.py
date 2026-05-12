from policyengine_uk.model_api import *


class solihull_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Solihull Council Tax Reduction assessed weekly income"
    documentation = "Weekly assessed income of the claimant and partner used to look up the Solihull banded discount table. Non-UC cases use claimant-and-partner net earnings (Section 20.3: gross less income tax, primary Class 1 National Insurance, half of any occupational pension contribution and half of any qualifying personal pension contribution, plus the Schedule 4 paragraph 1 earnings disregard of 50 pounds per week with paragraph 2 limiting it to one disregard per applicant). Source-countable non-earnings income is added; Schedule 2 disregards DLA / PIP / AFIP / attendance allowance / war mobility supplement (paragraphs 9-12), Child Maintenance (paragraph 47), Child Benefit (paragraph 63), the Employment and Support Allowance support component (paragraph 67) and Carer's Allowance (paragraph 74). Schedule 2 paragraph 75 applies a further 50 pound weekly disregard from income where any of the applicant, their partner or a dependent child is disabled (in receipt of Personal Independence Payment, an Armed Forces Independence Payment or Disability Living Allowance) - a single family-level disregard, not per qualifying member. AFIP is detected via the PolicyEngine UK armed_forces_independence_payment variable (the dedicated AFIP measure) rather than the broader afcs (Armed Forces Compensation Scheme aggregate) so non-AFIP AFCS payments such as Guaranteed Income Payments do not trigger the disregard. Universal Credit cases follow Section 12.2: counted income is the DWP-assessed UC award (universal_credit_pre_benefit_cap) less the Section 12.3 listed elements (Housing, Limited Capability for Work / Work-Related Activity, Disabled Child and Carer - modelled here through PolicyEngine UK's uc_housing_costs_element, uc_carer_element and uc_disability_elements aggregate, plus any further source-listed component supplied via the Solihull source input), plus DWP-assessed UC earned income less the same Schedule 4 weekly earnings disregard. Schedule 2 paragraph 76 disregards 'any income that is deemed by the authority as unearned income' for UC applicants, so UC unearned income (state pension, savings interest etc as deemed by DWP for UC purposes) is excluded from counted CTR income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.solihull.council_tax_reduction
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
        # Section 12.3 disregards the Housing, LCW/LCWRA, Disabled Child and
        # Carer elements. PolicyEngine UK's uc_disability_elements covers
        # LCWRA + disabled-child; standalone LCW and any future source-listed
        # component flow through the source input.
        disregarded_uc_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_carer_element",
                "uc_disability_elements",
                "solihull_council_tax_reduction_source_disregarded_uc_elements",
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
        # Schedule 2 paragraph 76 disregards "any income that is deemed by the
        # authority as unearned income" for UC applicants. PolicyEngine UK's
        # uc_unearned_income represents the DWP-assessed UC unearned income
        # (state pension, savings interest, etc.), which the authority treats
        # as the unearned-income measure for UC cases. The disregard means UC
        # counted income consists of only the residual UC award after Section
        # 12.3 element disregards plus DWP-assessed UC earned income net of
        # the Schedule 4 weekly disregard.
        uc_income = countable_uc_award + countable_uc_earned_income

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
        # Schedule 4 paragraphs 1-2: the earnings disregard applies only
        # where the applicant or partner has earnings, with one disregard
        # per applicant.
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
        # Schedule 2 paragraph 74 disregards Carer's Allowance and paragraph
        # 67 disregards the ESA support component, but PolicyEngine UK does
        # not separate the support component from the contributory ESA award
        # so esa_contrib is included in countable income as a known
        # approximation, consistent with other CTR implementations.
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

        # Schedule 2 paragraph 75: family-level 50 pound weekly disregard
        # from income where the applicant, their partner OR any dependent
        # child receives PIP / AFIP / DLA. The source wording reads as a
        # single disregard for the family (not per qualifying member). AFIP
        # is detected through armed_forces_independence_payment (the
        # PolicyEngine UK AFIP measure) rather than the broader afcs
        # aggregate, so non-AFIP AFCS payments such as Guaranteed Income
        # Payments do not trigger the disregard.
        family_disability = benunit.any(
            (person("pip", period) > 0)
            | (person("dla", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
        )
        annual_family_disregard = (
            family_disability * ctr.disability_disregard.amount * WEEKS_IN_YEAR
        )
        annual_income = max_(0, annual_income - annual_family_disregard)
        return annual_income / WEEKS_IN_YEAR
