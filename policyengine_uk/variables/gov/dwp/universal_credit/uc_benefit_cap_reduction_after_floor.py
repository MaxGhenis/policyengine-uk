from policyengine_uk.model_api import *


class uc_benefit_cap_reduction_after_floor(Variable):
    label = "UC benefit cap reduction after the protected floor"
    documentation = (
        "Benefit cap reduction actually taken off this benefit unit's "
        "Universal Credit award. Under current law it equals "
        "benefit_cap_reduction, except that it never exceeds the award left "
        "after deductions (the cap cannot take an award below nil). Where a "
        "protected minimum floor is in force, the cap reduction absorbs the "
        "floor first, so only the part of it fitting in the allowance "
        "uc_deductions leaves is applied. benefit_cap_reduction itself stays "
        "gross, because it also applies to Housing Benefit, which the "
        "Universal Credit floor does not protect."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        reduction = benunit("benefit_cap_reduction", period)
        deductions = benunit("uc_deductions", period)
        # Deductions take their share of the floor allowance first, so the
        # cap reduction is what bends when the floor binds. Under the Fair
        # Repayment Rate the 15% deductions cap equals a typical 15% floor
        # allowance, so cappable deductions alone essentially never breach
        # the floor - only benefit cap reductions push past it. JRF's worked
        # example (standard allowance £92, deduction £14, benefit cap £59,
        # floor £78) limits the total reduction to £14; keeping the £14
        # deduction and dropping the £59 cap reduction is consistent with it.
        headroom = max_(benunit("uc_maximum_reduction", period) - deductions, 0)
        # The award cannot go below nil, so the reduction actually applied
        # never exceeds what is left of the award after deductions.
        award_left = max_(
            benunit("universal_credit_pre_benefit_cap", period) - deductions, 0
        )
        return min_(min_(reduction, headroom), award_left)
