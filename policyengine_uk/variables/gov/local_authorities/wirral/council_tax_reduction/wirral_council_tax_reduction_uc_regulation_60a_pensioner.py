from policyengine_uk.model_api import *


class wirral_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Wirral CTR pension-age regulation 60A UC carve-out"
    documentation = "Whether a pension-age Universal Credit applicant under the Wirral 2026/27 Council Tax Reduction Scheme falls within Section 1.4(2)(b) - 'where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies in respect of the award'. Where true, the UC award is disregarded for the purposes of the local working-age routing, so the applicant remains on the prescribed pensioner scheme. PolicyEngine UK does not detect regulation 60A status from the underlying microdata, so this is exposed as a source input that defaults to False."
    definition_period = YEAR
    reference = "https://www.wirral.gov.uk/files/wirral-ctr-s13a-2026-27-scheme.pdf/download?inline"

    def formula(benunit, period, parameters):
        return False
