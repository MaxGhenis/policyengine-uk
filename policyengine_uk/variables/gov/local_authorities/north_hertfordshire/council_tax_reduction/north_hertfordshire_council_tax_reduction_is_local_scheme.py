from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_north_hertfordshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class north_hertfordshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under North Hertfordshire's local Council Tax Reduction scheme"
    documentation = "Section 1.6 and Class D of the North Hertfordshire 2026/27 scheme cover working-age applicants and pension-age applicants whose claimant or partner is on Income Support, income-based Jobseeker's Allowance, income-related Employment and Support Allowance or Universal Credit. Pension-age applicants outside those local cases stay on the prescribed pensioner scheme via simulated_council_tax_reduction_benunit. Section 1.4(2) disregards the Universal Credit award during the relevant period or where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme. The working-age branch uses 'any working-age adult in the benefit unit' rather than 'applicant/head is working-age'. Class D paragraph (a) reads 'the individual (or partner) must have not attained the qualifying age for state pension credit', which supports an applicant-or-partner test; Section 1.4(1)(a)'s narrower 'pensioner' definition is applicant-keyed (a pension-age applicant with a working-age partner and no passport is still a 'pensioner'). PolicyEngine UK does not expose a benefit-unit applicant/head pension-age flag distinct from the partner's, so the implementation follows Class D's more permissive wording, consistent with every other PolicyEngine UK CTR scheme that uses a benunit-wide working-age test."
    definition_period = YEAR
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        has_working_age_adult = benunit.any(
            person("is_adult", period) & ~person("is_SP_age", period)
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        uc_exception = benunit(
            "north_hertfordshire_council_tax_reduction_uc_regulation_60a_pensioner",
            period,
        ) | benunit(
            "north_hertfordshire_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        )
        local_case = (
            has_working_age_adult
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (
            (country == Country.ENGLAND)
            & is_north_hertfordshire(local_authority)
            & local_case
        )
