from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class solihull_council_tax_reduction_individual_non_dependant_deduction(Variable):
    value_type = float
    entity = Person
    label = "Solihull individual Council Tax Reduction non-dependant deduction"
    documentation = "Section 48.5 of the 2026/27 scheme applies a flat 10 pound weekly deduction for each non-dependant residing in the applicant's dwelling. Section 48.6 waives all non-dependant deductions where the applicant would have received a disability premium under the prescribed pensioner scheme (approximated here through the shared council_tax_reduction_household_has_non_dep_exemption helper: registered blind / Attendance Allowance / DLA care / PIP daily living / AFIP). Full-time student non-dependants are exempt via the shared is_full_time_student_non_dep helper, consistent with the project-wide CTR pattern."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.solihull.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "solihull_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        exempt = claimant_exempt | is_full_time_student_non_dep(person, period)
        weekly_amount = ctr.non_dependant_deduction.per_non_dependant
        return local_scheme * where(exempt, 0, weekly_amount * WEEKS_IN_YEAR)
