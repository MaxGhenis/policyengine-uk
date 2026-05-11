from policyengine_uk.model_api import *


class castle_point_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Castle Point CTR source-listed disregarded Universal Credit elements not otherwise represented"
    documentation = "Schedule 2 paragraph 34 disregards named Universal Credit elements from income. This source input covers any source-listed UC element amount not otherwise separately exposed in PolicyEngine UK, such as a legacy Limited Capability for Work element."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"
    default_value = 0
