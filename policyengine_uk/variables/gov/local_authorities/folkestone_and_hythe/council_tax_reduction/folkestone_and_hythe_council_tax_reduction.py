from policyengine_uk.model_api import *


class folkestone_and_hythe_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Folkestone and Hythe Council Tax Reduction"
    documentation = "Folkestone and Hythe District Council operates a Banded Discount Scheme under section 13A of the Local Government Finance Act 1992 for working-age applicants. Schedule 1 paragraph 1 sets four income bands of 100, 75, 50 and 25 per cent (zero above the Band 4 thresholds) indexed by household type (single / couple with no children / household with one child / household with two or more children, capped at two dependants by Schedule 1 paragraph 4). Schedule 1 paragraph 7 places applicants on Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance at Band 1 (100 per cent). Schedule 1 paragraph 5 strictly excludes applicants whose capital is greater than 16,000 pounds; Schedule 3 contains the standard Default Scheme capital disregards but no wholesale capital disregard for passported applicants, so income-based-benefit recipients with capital above 16,000 pounds are still excluded. Section 27.1 applies tariff income of 1 pound per week for every 250 pounds or part thereof of capital above 6,000 pounds. Section 39.1(a) caps eligible council tax at the Band D equivalent for the dwelling. Section 39.5 deducts 10 pounds per week per non-dependant after the band percentage, with Section 39.6 exemptions for JSA-IB, ESA-IR, IS, PC Guarantee Credit and UC with no earnings, and Section 39.7 collapses a non-dependant couple's deduction to a single highest-rate deduction. Pension-age applicants whose claimant or partner is on Income Support, income-based JSA, income-related ESA or Universal Credit stay in the local working-age banded scheme (Section 1.6 and Class D); Section 1.4(2) disregards the Universal Credit award during the relevant period or where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.folkestone_and_hythe.council_tax_reduction
        local_scheme = benunit(
            "folkestone_and_hythe_council_tax_reduction_is_local_scheme", period
        )
        rate = benunit("folkestone_and_hythe_council_tax_reduction_band_rate", period)
        liability = benunit.household(
            "folkestone_and_hythe_council_tax_reduction_maximum_eligible_liability",
            period,
        )
        non_dep_deductions = benunit(
            "folkestone_and_hythe_council_tax_reduction_non_dep_deductions", period
        )
        # Section 27.1 and Schedule 1 paragraph 5: apply the 16,000 pound strict
        # cutoff to household savings for non-UC cases and to DWP-assessed UC
        # capital (Section 13.4) for UC cases. Schedule 3 does not include a
        # wholesale capital disregard for IS / income-based JSA / income-related
        # ESA, so passported applicants with capital above 16,000 are still
        # excluded.
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        award = max_(0, liability * rate - non_dep_deductions)
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
