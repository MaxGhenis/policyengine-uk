from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class folkestone_and_hythe_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Folkestone and Hythe maximum Council Tax liability eligible for Council Tax Reduction"
    documentation = "Section 39.1(a) of the adopted 2026/27 scheme caps the eligible council tax for the calculation of the reduction at the lower of the actual council tax for the dwelling or the Band D amount for the relevant financial year."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"

    def formula(household, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            local_authorities.england.council_tax.band_ratio,
        )
        cap_band_ratio = local_authorities.folkestone_and_hythe.council_tax_reduction.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        return where(band_ratio > cap_band_ratio, capped_liability, council_tax)
