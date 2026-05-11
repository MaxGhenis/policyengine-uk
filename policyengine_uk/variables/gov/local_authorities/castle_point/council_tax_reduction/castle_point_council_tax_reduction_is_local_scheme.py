from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_castle_point,
)
from policyengine_uk.variables.household.demographic.country import Country


class castle_point_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Castle Point's local Council Tax Reduction scheme"
    documentation = "Paragraphs 1.2 and 1.3 confirm that the working-age scheme applies to non-pensioners (plus pension-age applicants on a working-age income-related benefit or Universal Credit). Paragraph 1(2) disregards pension-age Universal Credit awards during the relevant period and where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, leaving those cases on the prescribed pensioner scheme."
    definition_period = YEAR
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"

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
            "castle_point_council_tax_reduction_uc_relevant_period_pensioner", period
        ) | benunit(
            "castle_point_council_tax_reduction_uc_regulation_60a_pensioner", period
        )
        local_case = (
            has_working_age_adult
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (
            (country == Country.ENGLAND) & is_castle_point(local_authority) & local_case
        )
