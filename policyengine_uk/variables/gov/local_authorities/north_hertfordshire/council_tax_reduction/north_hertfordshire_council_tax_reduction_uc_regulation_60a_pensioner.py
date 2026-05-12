from policyengine_uk.model_api import *


class north_hertfordshire_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "North Hertfordshire regulation 60A Universal Credit pensioner exception"
    documentation = "Section 1.4(2)(b) of the North Hertfordshire 2026/27 scheme disregards an applicant's Universal Credit award where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies during the relevant period. The applicant is then treated as a pensioner and remains on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.north-herts.gov.uk/sites/default/files/2026-03/North%20Herts%20S13A%20202627%20Scheme%20FINAL.pdf"
    default_value = False
