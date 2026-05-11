from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_sevenoaks,
)
from policyengine_uk.variables.household.demographic.country import Country


class sevenoaks_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Sevenoaks's local Council Tax Reduction scheme"
    documentation = "Section 1.1 of the Sevenoaks 2026/27 scheme covers working-age applicants and pension-age applicants whose claimant or partner is on Income Support, income-based Jobseeker's Allowance, income-related Employment and Support Allowance or Universal Credit. Pension-age applicants outside those local cases stay on the prescribed pensioner scheme via simulated_council_tax_reduction_benunit. The adopted scheme has no regulation 60A or relevant-period Universal Credit carve-out for pensioners — pension-age UC awards remain in the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.sevenoaks.gov.uk/download/downloads/id/4481/council_tax_support_local_scheme_202627.docx"

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
        local_case = (
            has_working_age_adult | relevant_income_based_benefit | has_uc_award
        )
        return (country == Country.ENGLAND) & is_sevenoaks(local_authority) & local_case
