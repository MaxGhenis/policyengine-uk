from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wealden_working_age,
)


class wealden_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Wealden Council Tax Reduction"
    documentation = "Wealden District Council operates a Banded Discount Scheme under section 13A of the Local Government Finance Act 1992 for working-age applicants. The council's working-age scheme page (effective 1 April 2026) sets four income bands of 100, 60, 40, 80 and 20 per cent (zero above the Band 4 thresholds) — discount rates of 100/80/60/40/0 per cent — indexed by household type (single / couple with no children / family with one child / family with two or more children). The dependant count is capped at two for the band column. The scheme has no Band cap and no working-age non-dependant deductions (`There are no deductions for any non dependants living with you`). Applicants whose capital is more than 6,000 pounds receive no support; the same 6,000 pound strict cutoff is applied to DWP-assessed Universal Credit capital for UC cases. Pension-age applicants are routed to the prescribed pensioner scheme; the council's working-age page does not describe a pension-age UC local-rule carve-out, so this implementation treats all pension-age applicants as falling outside the local working-age scheme."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.wealden.gov.uk/benefits/who-can-get-council-tax-reduction/"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wealden.council_tax_reduction
        working_age = is_wealden_working_age(
            benunit.household("local_authority", period),
            benunit.household("country", period),
            benunit.household("council_tax_reduction_household_has_pensioner", period),
        )
        rate = benunit("wealden_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
