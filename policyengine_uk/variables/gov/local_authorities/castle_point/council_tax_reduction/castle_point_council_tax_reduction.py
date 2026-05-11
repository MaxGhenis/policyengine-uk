from policyengine_uk.model_api import *


class castle_point_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Castle Point Council Tax Reduction"
    documentation = "Castle Point operates a Banded Discount Scheme with a 70 per cent maximum (paragraph 43.1). Schedule 1 paragraph 1 sets the entitlement percentage from a six-row, seven-column table indexed by household type (single / couple x no / one / two or more children) and weekly net income (Passported plus six income tiers). Paragraph 30.1 and Schedule 1 paragraph 5 exclude applicants whose capital is greater than 6,000 pounds. Schedule 1 paragraph 3 places passported Income Support / income-related ESA or income-based JSA applicants at Band A (70 per cent). Paragraph 45.1 confirms there are no non-dependant deductions; there is no Band cap. Pension-age applicants follow the prescribed pensioner scheme except where paragraph 1 treats a pension-age Universal Credit or working-age income-related-benefit case as a person who is not a pensioner."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.castle_point.council_tax_reduction
        local_scheme = benunit(
            "castle_point_council_tax_reduction_is_local_scheme", period
        )
        rate = benunit("castle_point_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        # Paragraph 30.1 / Schedule 1 paragraph 5: "greater than 6,000" strict
        # cutoff, using DWP-determined UC capital for UC awards (paragraph 12.8).
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
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
