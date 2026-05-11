from policyengine_uk.model_api import *


class rochford_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Rochford's Universal Credit regulation 60A pensioner exception applies"
    )
    documentation = "Where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies to a pension-age applicant's Universal Credit award, the prescribed pensioner scheme classes treat the applicant as a pensioner and keep them on the national pensioner CTR scheme rather than Rochford's local working-age banded scheme."
    definition_period = YEAR
    reference = (
        "https://www.rochford.gov.uk/local-council-tax-support-for-working-age-people"
    )
    default_value = False
