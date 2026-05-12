from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class wirral_council_tax_reduction_individual_non_dependant_deduction(Variable):
    value_type = float
    entity = Person
    label = "Wirral individual Council Tax Reduction non-dependant deduction"
    documentation = "Section 48A.1 of the 2026/27 scheme applies a flat 5 pound weekly deduction for each non-dependant residing in the applicant's dwelling. Section 48A.4 waives all non-dependant deductions if the applicant or partner is registered blind or in receipt of Attendance Allowance, the care component of Disability Living Allowance, the daily living component of Personal Independence Payment or an Armed Forces Independence Payment. Section 48A.5(c) waives the deduction for a full-time student non-dependant. The shared is_full_time_student_non_dep helper marks any non-dependant whose current_education is not NOT_IN_EDUCATION (or who is in higher education) as a full-time student, consistent with the strictness available in PolicyEngine UK's microdata; the helper is project-wide and does not distinguish between full-time and part-time enrolment at the secondary or post-secondary level. PolicyEngine UK does not currently model the other narrow Section 48A.5 / 48A.6 non-dependant-side exemptions (training allowance under section 2 of the 1973 Act / Enterprise and New Towns (Scotland) Act 1990, 52-week hospital patient, armed forces away on operations, Schedule 1 to the 1992 Act CT-discount-disregards), so a non-dependant who would qualify for one of those exemptions but is not a full-time student receives the deduction as a known approximation."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.wirral.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "wirral_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        exempt = claimant_exempt | is_full_time_student_non_dep(person, period)
        weekly_amount = ctr.non_dependant_deduction.per_non_dependant
        return local_scheme * where(exempt, 0, weekly_amount * WEEKS_IN_YEAR)
