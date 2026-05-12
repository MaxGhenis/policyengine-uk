from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class wirral_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Wirral maximum Council Tax liability eligible for Council Tax Reduction"
    documentation = "Section 48.0 of the adopted 2026/27 scheme caps the council tax amount (`A`) used to calculate maximum Council Tax Reduction at Band D liability: 'This amount is capped at Band D liability.' For dwellings in Bands E-H the eligible liability is the Band D equivalent calculated using the English Council Tax band ratio table."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(household, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            local_authorities.england.council_tax.band_ratio,
        )
        cap_band_ratio = local_authorities.wirral.council_tax_reduction.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        return where(band_ratio > cap_band_ratio, capped_liability, council_tax)
