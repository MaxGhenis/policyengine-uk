from policyengine_uk.model_api import *


class rother_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Rother Universal Credit relevant-period pensioner exception"
    documentation = "Section 1.4(2)(a) of the Rother 2026/27 scheme disregards an applicant's Universal Credit award during the relevant period (Section 1.4(3): the period beginning when P and each partner has attained the qualifying age for state pension credit and ending when the last assessment period for UC ends). The applicant is then treated as a pensioner and remains on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"
    default_value = False
