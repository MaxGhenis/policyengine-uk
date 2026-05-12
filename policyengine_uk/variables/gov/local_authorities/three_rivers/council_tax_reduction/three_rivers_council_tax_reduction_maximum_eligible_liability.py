from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class three_rivers_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = (
        "Three Rivers maximum Council Tax liability eligible for Council Tax Reduction"
    )
    documentation = "The council's working-age scheme page caps eligible council tax at the Band D equivalent for the dwelling: `the scheme applies to properties in Council Tax Band D; for bands E-H, reductions are calculated as a percentage of equivalent Band D charges`."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.threerivers.gov.uk/services/counciltax/ctrs"

    def formula(household, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            local_authorities.england.council_tax.band_ratio,
        )
        cap_band_ratio = local_authorities.three_rivers.council_tax_reduction.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        return where(band_ratio > cap_band_ratio, capped_liability, council_tax)
