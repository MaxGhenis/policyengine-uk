from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction_source_disregarded_uc_elements(
    Variable
):
    value_type = float
    entity = BenUnit
    label = "North Hertfordshire Council Tax Reduction source-listed disregarded Universal Credit elements"
    documentation = "Annual amount of any source-listed Universal Credit element disregarded by North Hertfordshire's 2026/27 scheme that is not separately modelled in PolicyEngine UK. Section 12.3 of the formal scheme allows the authority to adjust the DWP-assessed UC income to disregard the housing-costs element and any other sums to be disregarded in the calculation of earnings or income other than earnings. The implementation automatically subtracts the modelled housing-costs element; this source input covers any other adjustment supplied by the council."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"
    default_value = 0
