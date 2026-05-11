from policyengine_uk.model_api import *


class folkestone_and_hythe_council_tax_reduction_weekly_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Folkestone and Hythe Council Tax Reduction weekly tariff income"
    documentation = "Section 27.1 of the 2026/27 scheme adds 1 pound per week of weekly income for every 250 pounds or part thereof of capital above the disregard level of 6,000 pounds. For UC cases, the DWP-determined Universal Credit capital is used in place of household savings (Section 13.4)."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.folkestone_and_hythe.council_tax_reduction
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
        # 1 pound per week for every 250 pounds or part thereof above 6,000.
        blocks = where(
            excess_capital > 0,
            np.ceil(excess_capital / ctr.means_test.tariff_block),
            0,
        )
        return blocks * ctr.means_test.tariff_amount
