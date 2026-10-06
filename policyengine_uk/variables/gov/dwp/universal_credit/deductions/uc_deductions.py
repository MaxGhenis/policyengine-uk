from policyengine_uk.model_api import *


class uc_deductions(Variable):
    label = "UC deductions"
    documentation = (
        "Money deducted from this benefit unit's Universal Credit award to "
        "repay debts: advance repayments, government debt (benefit and tax "
        "credit overpayments) and third party deductions. Deductions leave "
        "at least one penny per assessment period payable (Schedule 6, "
        "paragraph 3(1)(a) of SI 2013/380). Per-household statistics are "
        "validated against the DWP deductions statistics; weighted "
        "aggregates are not, because they scale with the model's UC "
        "caseload, which falls short of the administrative count. "
        "Annualized from the surveyed monthly rate: for deduction types "
        "with spells shorter than a year (e.g. advance recovery), annual "
        "per-household amounts are upper bounds."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        requested = benunit("uc_deduction_rate", period) * benunit(
            "uc_standard_allowance", period
        )
        pre_cap = benunit("universal_credit_pre_benefit_cap", period)
        gross_cap_reduction = benunit("benefit_cap_reduction", period)
        minimum_payable = p.minimum_payable * MONTHS_IN_YEAR
        allowance = benunit("uc_maximum_reduction", period)
        # Current law: deductions come out of the award the benefit cap
        # leaves, and must leave one penny per assessment period payable.
        current_law = min_(
            requested,
            max_(max_(pre_cap - gross_cap_reduction, 0) - minimum_payable, 0),
        )
        # The protected minimum floor (zero, and so inactive, under current
        # law) limits deductions and benefit cap reductions combined, and the
        # benefit cap reduction absorbs it first: deductions keep their share
        # of the floor allowance, and the cap reduction takes what is left.
        # The one-penny test then runs against the award after the cap
        # reduction that actually applies, not the gross one. That reduction
        # is computed here from the gross reduction and the allowance, so
        # uc_deductions never reads uc_benefit_cap_reduction_after_floor
        # (which reads uc_deductions) and there is no cycle.
        floor_share = min_(requested, allowance)
        cap_reduction_applied = min_(
            gross_cap_reduction, max_(allowance - floor_share, 0)
        )
        award_carries_both = (allowance < np.inf) & (
            pre_cap - minimum_payable >= floor_share + cap_reduction_applied
        )
        # Where the award cannot carry both, the penny rule binds and the
        # deduction falls back to the current-law amount, limited by the
        # floor. The floor binds on the above-cap excess too (last resort and
        # child maintenance deductions); JRF's briefing does not say whether
        # their floor exempts those categories, so this is a modeling choice.
        return where(award_carries_both, floor_share, min_(current_law, allowance))
