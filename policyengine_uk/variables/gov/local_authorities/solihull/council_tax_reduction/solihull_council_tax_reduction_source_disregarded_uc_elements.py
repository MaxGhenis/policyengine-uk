from policyengine_uk.model_api import *


class solihull_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Solihull CTR source-supplied additional disregarded Universal Credit elements"
    )
    documentation = "Annual amount of Universal Credit components disregarded under Section 12.3 of the Solihull 2026/27 scheme that are not already covered by PolicyEngine UK's modelled UC element variables (uc_housing_costs_element, uc_carer_element, uc_disability_elements). Solihull's Section 12.3 lists the Housing, Limited Capability for Work / Work-Related Activity, Disabled Child and Carer elements; PolicyEngine UK's uc_disability_elements covers LCWRA and disabled-child. Standalone LCW and any future scheme adjustments can be passed in through this source input. Defaults to zero so the implementation matches the explicit Section 12.3 list."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        return 0
