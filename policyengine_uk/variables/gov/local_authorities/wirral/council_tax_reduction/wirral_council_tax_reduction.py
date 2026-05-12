from policyengine_uk.model_api import *


class wirral_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Wirral Council Tax Reduction"
    documentation = "Wirral Metropolitan Borough Council operates a banded discount Council Tax Reduction Scheme under section 13A of the Local Government Finance Act 1992 for working-age applicants from 1 April 2026. Schedule 1 paragraph 1 sets a six-column by five-band income table with discount rates of 50, 40, 30, 20 and 0 per cent (the Council's maximum support rate is 50 per cent, so Band 1 is the maximum) indexed by household type (single / single with one dependant / single with 2+ dependants; couple / couple with one dependant / couple with 2+ dependants). Schedule 1 caps the band column at 2+ dependants. Section 48.0 also caps eligible council tax at the Band D equivalent for the dwelling. Schedule 1 paragraph 5 and Class D paragraph (g) strictly exclude applicants whose capital is 6,000 pounds or above, with the same 6,000 pound cutoff applied to DWP-assessed Universal Credit capital under Section 12.5 for UC cases. Schedule 1 paragraph 7 places applicants on Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance at Band 1 (50 per cent). Section 48A.1 reduces eligible council tax by 5 pounds per week per non-dependant before the band rate is applied (consistent with the Wirral Summary Guide worked example, where 40 per cent of (30 - 5) = 10 pound per week); Section 48A.2 collapses a non-dependant couple's deductions into a single deduction; Section 48A.4 waives all non-dependant deductions if the applicant or partner is registered blind or in receipt of Attendance Allowance, the care component of Disability Living Allowance, the daily living component of Personal Independence Payment or an Armed Forces Independence Payment; Section 48A.5(c) waives the deduction for a full-time student non-dependant. Section 1.6 and Class D route pension-age applicants whose claimant or partner is on Income Support, income-based JSA, income-related ESA or Universal Credit into the local working-age banded scheme; Section 1.4(2) disregards the UC award during the relevant period or where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wirral.council_tax_reduction
        local_scheme = benunit("wirral_council_tax_reduction_is_local_scheme", period)
        rate = benunit("wirral_council_tax_reduction_band_rate", period)
        liability = benunit.household(
            "wirral_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "wirral_council_tax_reduction_non_dependant_deductions", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Class D paragraph (g) and Schedule 1 paragraph 5 use the wording
        # "6,000 pounds or above" - a strict >=6,000 cutoff (not >). For UC
        # cases Section 12.5 substitutes the DWP-assessed UC capital.
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital < ctr.means_test.capital_limit
        net_liability = max_(0, liability - non_dep_deductions)
        award = net_liability * rate
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
