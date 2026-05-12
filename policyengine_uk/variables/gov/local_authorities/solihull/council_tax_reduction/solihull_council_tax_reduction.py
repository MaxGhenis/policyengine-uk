from policyengine_uk.model_api import *


class solihull_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Solihull Council Tax Reduction"
    documentation = "Solihull Metropolitan Borough Council operates a banded discount Council Tax Reduction Scheme under section 13A of the Local Government Finance Act 1992 for working-age applicants from 2026/27. Schedule 1 paragraph 1 sets a six-column by five-band income table with discount rates of 85, 75, 50, 25 and 0 per cent indexed by household type (Single / Single with 1 Child / Single with 2+ Children; Couples / Couple with 1 Child / Couple with 2+ Children). Schedule 1 caps the band column at 2+ children. Class D paragraph (g) and Schedule 1 paragraph 5 strictly exclude applicants whose capital is 16,000 pounds or above, with the same 16,000 pound cutoff applied to DWP-assessed Universal Credit capital under Section 12.5 for UC cases. Schedule 1 paragraph 7 places applicants on Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance at Band 1 (85 per cent). Section 48.5 reduces the Council Tax Reduction by 10 pounds per week for each non-dependant residing in the household, after the band percentage; Section 48.6 waives all non-dependant deductions where the applicant would have received a disability premium (approximated through the shared council_tax_reduction_household_has_non_dep_exemption helper). Section 1.6 and Class D route pension-age applicants whose claimant or partner is on Income Support, income-based JSA, income-related ESA or Universal Credit into the local working-age banded scheme; Section 1.4(2) disregards the UC award during the relevant period or where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.solihull.council_tax_reduction
        local_scheme = benunit("solihull_council_tax_reduction_is_local_scheme", period)
        rate = benunit("solihull_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "solihull_council_tax_reduction_non_dependant_deductions", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Class D paragraph (g) and Schedule 1 paragraph 5 use the wording
        # "16,000 pounds or above" - a strict >=16,000 cutoff (not >). For UC
        # cases Section 12.5 substitutes the DWP-assessed UC capital.
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital < ctr.means_test.capital_limit
        award = max_(0, liability * rate - non_dep_deductions)
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
