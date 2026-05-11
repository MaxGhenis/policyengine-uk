from policyengine_uk.model_api import *


class rother_council_tax_reduction_weekly_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rother Council Tax Reduction weekly tariff income"
    documentation = "Section 28.2 of the 2026/27 scheme treats capital above 6,000 pounds as weekly tariff income of 1 pound for each complete 250 pounds, and Section 28.3 includes any incomplete final block at the same 1 pound per week. For UC cases, Section 13.4 substitutes the DWP-determined Universal Credit capital for household savings."
    definition_period = YEAR
    unit = GBP
    reference = "https://rdcpublic.blob.core.windows.net/website-uploads/2025/03/Rother-Council-Tax-Reduction-Scheme-2025-26.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.rother.council_tax_reduction
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
        excess_capital = max_(0, capital - ctr.means_test.tariff_threshold)
        # 1 pound per week per complete 250 pounds plus any incomplete remainder.
        blocks = where(
            excess_capital > 0,
            np.ceil(excess_capital / ctr.means_test.tariff_block),
            0,
        )
        return blocks * ctr.means_test.tariff_amount
