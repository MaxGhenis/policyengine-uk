from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "North Hertfordshire Council Tax Reduction"
    documentation = "North Hertfordshire District Council operates a Banded Discount Scheme under section 13A of the Local Government Finance Act 1992 for working-age applicants. Schedule 1 paragraph 1 of the 2026/27 scheme sets five income bands of 100, 75, 45 and 25 per cent (zero above the Band 4 thresholds) indexed by household type (single / single + 1 / single + 2 / single + 3 children; couple / couple + 1 / couple + 2 / couple + 3 children). Schedule 1 paragraph 4 caps the dependant count at three. Schedule 1 paragraph 7 places passported Income Support, income-related Employment and Support Allowance or income-based Jobseeker's Allowance applicants at Band 1 (100 per cent). Section 26.1, Section 27.1 and Schedule 1 paragraph 5 strictly exclude applicants whose capital is greater than 16,000 pounds; Section 11.1 treats partner capital as the applicant's, so the source cutoff is on applicant-and-partner capital only. PolicyEngine UK does not currently expose an applicant-and-partner capital variable, so this implementation uses household savings as a known proxy in line with every other PolicyEngine UK CTR scheme; in practice a non-dependant's separately-held savings could in principle push the household total above the limit even when applicant-and-partner capital is below. Schedule 3 contains the standard Default Scheme capital disregards but no wholesale capital disregard for the passported benefits, so income-based-benefit recipients with capital above 16,000 pounds are still excluded. The 2026/27 scheme has no tariff income on capital below the limit, no Band cap, no minimum award and no working-age non-dependant deductions. Pension-age applicants whose claimant or partner is on Income Support, income-based JSA, income-related ESA or Universal Credit stay in the local working-age banded scheme (Section 1.6 and Class D); Section 1.4(2) disregards the Universal Credit award during the relevant period or where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_hertfordshire.council_tax_reduction
        local_scheme = benunit(
            "north_hertfordshire_council_tax_reduction_is_local_scheme", period
        )
        rate = benunit("north_hertfordshire_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        # Section 26.1 and Schedule 1 paragraph 5: apply the 16,000 pound strict
        # cutoff to household savings for non-UC cases and to DWP-assessed UC
        # capital (Section 12.5) for UC cases. Schedule 3 does not include a
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
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
