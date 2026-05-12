from policyengine_uk.model_api import *


class solihull_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Solihull CTR pension-age UC relevant-period carve-out"
    documentation = "Whether a pension-age Universal Credit applicant under the Solihull 2026/27 Council Tax Reduction Scheme falls within Section 1.4(2)(a) and 1.4(3) - 'during the relevant period' - where 'relevant period' means the period beginning with the day on which P and each partner of P has attained the qualifying age for state pension credit and ending with the day on which the last UC assessment period ends. Where true, the UC award is disregarded for the purposes of the local working-age routing, so the applicant remains on the prescribed pensioner scheme. PolicyEngine UK does not track UC assessment periods at the day level from the underlying microdata, so this is exposed as a source input that defaults to False."
    definition_period = YEAR
    reference = "https://www.solihull.gov.uk/sites/default/files/2026-02/Council-Tax-Reduction-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        return False
