from policyengine_uk.model_api import *


class wirral_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Wirral CTR source-supplied additional disregarded Universal Credit elements"
    )
    documentation = "Annual amount of Universal Credit components disregarded under Section 12.3 of the Wirral 2026/27 scheme that are not already covered by PolicyEngine UK's modelled UC element variables (uc_housing_costs_element, uc_carer_element, uc_disability_elements). Wirral's Section 12.3 lists the Housing, Limited Capability for Work / Work-Related Activity, Disabled Child, Carer and Child Care elements. PolicyEngine UK's uc_disability_elements covers LCWRA and disabled-child; standalone LCW (where applicable) and any future scheme adjustments can be passed in through this source input. Defaults to zero so the implementation matches the explicit Section 12.3 list."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        return 0
