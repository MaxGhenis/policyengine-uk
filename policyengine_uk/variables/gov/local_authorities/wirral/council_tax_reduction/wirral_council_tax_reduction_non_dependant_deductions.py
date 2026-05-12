from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class wirral_council_tax_reduction_non_dependant_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Wirral Council Tax Reduction non-dependant deductions"
    documentation = "Section 48A.1 of the 2026/27 scheme reduces eligible council tax by 5 pounds per week for each non-dependant residing in the dwelling. Section 48A.2 collapses two non-dependants who are a member of a couple into a single deduction. The Summary Guide worked example applies the deduction to the council tax liability before the band rate, so the implementation deducts the non-dependant amount from the maximum eligible liability before applying the income-band percentage."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "wirral_council_tax_reduction_individual_non_dependant_deduction",
        )
