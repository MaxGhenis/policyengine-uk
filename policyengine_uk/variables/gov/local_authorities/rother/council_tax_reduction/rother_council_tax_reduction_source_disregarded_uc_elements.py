from policyengine_uk.model_api import *


class rother_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Rother Council Tax Reduction source-listed disregarded Universal Credit elements"
    documentation = "Annual amount of any source-listed Universal Credit element (under Section 13.2 of the Rother 2026/27 scheme) that is not separately modelled in PolicyEngine UK. Section 13.2 of the formal scheme names only the housing-costs element; the council's live working-age page also mentions the disabled child, limited capability for work and carer elements. Where the live page's broader list applies, the additional disregarded element amounts can be supplied through this Rother-scoped source input."
    definition_period = YEAR
    unit = GBP
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"
    default_value = 0
