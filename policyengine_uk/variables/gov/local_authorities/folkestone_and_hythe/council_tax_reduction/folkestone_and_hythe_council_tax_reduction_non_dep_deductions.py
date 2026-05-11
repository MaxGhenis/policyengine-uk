from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class folkestone_and_hythe_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Folkestone and Hythe Council Tax Reduction non-dependant deductions"
    documentation = "Section 39.5 of the adopted 2026/27 scheme applies a flat 10 pound weekly deduction per non-dependant after the band percentage. Section 39.7 applies a single deduction for couple non-dependants using the highest applicable rate; the source does not exclude Universal Credit awards from this one-deduction couple rule."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "folkestone_and_hythe_council_tax_reduction_individual_non_dep_deduction",
        )
