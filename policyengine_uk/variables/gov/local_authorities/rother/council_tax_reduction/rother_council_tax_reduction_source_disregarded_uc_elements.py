from policyengine_uk.model_api import *


class rother_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Rother Council Tax Reduction source-listed disregarded Universal Credit elements"
    documentation = "Annual amount of any source-listed Universal Credit element disregarded by Rother's 2026/27 scheme that is not separately modelled in PolicyEngine UK. The implementation automatically subtracts the modelled housing-costs, carer, disabled-child and LCWRA elements; this source input covers any remaining listed element such as a standalone Limited Capability for Work element where it differs from PolicyEngine UK's LCWRA variable."
    definition_period = YEAR
    unit = GBP
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"
    default_value = 0
