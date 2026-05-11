from policyengine_uk.model_api import *


class rochford_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Rochford CTS source-listed disregarded Universal Credit elements not"
        " otherwise represented"
    )
    documentation = "Rochford's working-age scheme page disregards named Universal Credit elements (Housing costs, Carer's, Limited Capability for Work, Disabled Child) from income. Modelled elements are subtracted directly from the UC award in the weekly-income calculation. This Rochford-scoped source input covers any source-listed UC element amount not otherwise separately exposed in PolicyEngine UK, such as a legacy stand-alone Limited Capability for Work element where only the LCWRA element is modelled."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.rochford.gov.uk/local-council-tax-support-for-working-age-people"
    )
    default_value = 0
