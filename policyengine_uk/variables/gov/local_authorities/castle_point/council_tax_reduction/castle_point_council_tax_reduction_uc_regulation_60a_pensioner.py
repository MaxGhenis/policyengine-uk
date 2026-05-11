from policyengine_uk.model_api import *


class castle_point_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Castle Point's Universal Credit regulation 60A pensioner exception"
        " applies"
    )
    documentation = "Castle Point paragraph 1(2)(b) disregards a pension-age applicant's Universal Credit award where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies, keeping the applicant on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"
    default_value = False
