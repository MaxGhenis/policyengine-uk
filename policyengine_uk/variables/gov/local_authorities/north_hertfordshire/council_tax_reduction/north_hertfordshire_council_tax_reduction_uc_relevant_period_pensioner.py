from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "North Hertfordshire Universal Credit relevant-period pensioner exception"
    documentation = "Section 1.4(2)(a) of the North Hertfordshire 2026/27 scheme disregards an applicant's Universal Credit award during the relevant period (the period beginning when P and each partner has attained the qualifying age for state pension credit and ending when the last assessment period for UC ends). The applicant is then treated as a pensioner and remains on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"
    default_value = False
