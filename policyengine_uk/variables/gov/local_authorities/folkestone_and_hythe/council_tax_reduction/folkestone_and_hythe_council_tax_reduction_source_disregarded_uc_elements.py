from policyengine_uk.model_api import *


class folkestone_and_hythe_council_tax_reduction_source_disregarded_uc_elements(
    Variable
):
    value_type = float
    entity = BenUnit
    label = "Folkestone and Hythe Council Tax Reduction source-listed disregarded Universal Credit elements"
    documentation = "Annual amount of any source-listed Universal Credit element (under Section 13.2) that is not separately modelled in PolicyEngine UK. Section 13.2 names the housing element, the limited capability for work and work-related activity (LCWRA) element, and transitional protection. PolicyEngine UK exposes housing and LCWRA directly; transitional protection and any other source-listed element must be supplied through this Folkestone and Hythe-scoped source input."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"
    default_value = 0
