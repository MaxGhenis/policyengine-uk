from policyengine_uk.model_api import *


class castle_point_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Castle Point Council Tax Reduction assessed weekly income"
    documentation = "Weekly net income of the claimant and partner used to look up the Schedule 1 entitlement bands. Paragraphs 12.4 to 12.7 use DWP-assessed Universal Credit income (multiplied by 12 and divided by 52) plus the gross Universal Credit award before any deductions for loans, sanctions, advances, third-party payments or payments to landlords (paragraph 12.5, modelled here as universal_credit_pre_benefit_cap). Paragraph 12.6 and Schedule 2 disregard source-listed UC elements from that award. Non-UC cases use the prescribed Schedule 2 disregards via council_tax_reduction_applicable_income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.castlepoint.gov.uk/documents/d/guest/castle-point-ctr-s13a-scheme-2026-final"

    def formula(benunit, period, parameters):
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # Paragraph 12.5: use the gross UC award before SoS deductions.
        countable_uc_award = max_(
            0,
            benunit("universal_credit_pre_benefit_cap", period)
            - add(
                benunit,
                period,
                [
                    "uc_housing_costs_element",
                    "uc_childcare_element",
                    "uc_carer_element",
                    "uc_LCWRA_element",
                    "castle_point_council_tax_reduction_source_disregarded_uc_elements",
                ],
            ),
        )
        uc_income = (
            benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period)
            + countable_uc_award
        )
        return where(
            has_uc_award,
            uc_income / WEEKS_IN_YEAR,
            benunit("council_tax_reduction_applicable_income", period) / WEEKS_IN_YEAR,
        )
