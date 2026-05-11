from policyengine_uk.model_api import *


class castle_point_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Castle Point's Universal Credit relevant-period pensioner exception"
        " applies"
    )
    documentation = "Castle Point paragraph 1(2)(a) disregards a pension-age applicant's Universal Credit award during the prescribed relevant period, keeping the applicant on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"
    default_value = False
