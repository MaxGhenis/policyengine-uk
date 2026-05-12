from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class solihull_council_tax_reduction_non_dependant_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Solihull Council Tax Reduction non-dependant deductions"
    documentation = "Section 48.5 of the 2026/27 scheme reduces the Council Tax Reduction by 10 pounds per week for each non-dependant residing in the household, after the band percentage. Section 48.6 waives all non-dependant deductions where the applicant would have received a disability premium under the prescribed pensioner scheme. The implementation applies the deduction after the band rate (matching the source's 'after the band percentage' phrasing); the Section 48.6 exemption is approximated through the shared council_tax_reduction_household_has_non_dep_exemption helper, which captures applicant or partner in receipt of Attendance Allowance, the care component of Disability Living Allowance, the daily living component of Personal Independence Payment, an Armed Forces Independence Payment or who is registered blind."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "solihull_council_tax_reduction_individual_non_dependant_deduction",
        )
