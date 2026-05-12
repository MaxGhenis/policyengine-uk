from policyengine_uk.model_api import *


class three_rivers_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Three Rivers Council Tax Reduction source-listed disregarded Universal Credit elements"
    documentation = "Annual amount of any source-listed Universal Credit element disregarded by Three Rivers's working-age scheme that is not separately modelled in PolicyEngine UK. The implementation automatically subtracts the modelled housing-costs, carer and disability (LCWRA plus disabled-child) elements; the council's live page also names the `Universal Credit Limited Capacity to Work Element`, which in PolicyEngine UK is treated as part of the LCWRA aggregate. This source input covers any remaining standalone element."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.threerivers.gov.uk/services/counciltax/ctrs"
    default_value = 0
