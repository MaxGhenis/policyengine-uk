# IMPACT STEP A1 (scratch, not committed): the three gates read only the
# claimant and partner, keeping the old benefit-unit-wide combination:
# no claimant or partner over state pension age, no claimant or partner
# income-related ESA, a claimant or partner reports Income Support.
from policyengine_uk.model_api import *


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        person = benunit.members
        cp = person("is_claimant_or_partner", period)
        youngest_child_5_or_under = (
            benunit("youngest_child_age_for_legacy_benefits", period)
            <= IS.eligibility.lone_parent_youngest_child_age_limit
        )
        lone_parent_with_young_child = (
            benunit("is_lone_parent", period) & youngest_child_5_or_under
        )
        cp_cares = benunit.any(cp & person("is_carer_for_benefits", period))
        none_SP_age = ~benunit.any(cp & person("is_SP_age", period))
        reported = benunit.sum(person("esa_income_reported", period) * cp)
        income_related_esa = where(
            add(benunit, period, ["esa_income_reported"]) > 0,
            benunit("esa_income_eligible", period)
            & (reported > benunit("esa_income_tariff_income", period)),
            benunit("esa_income", period) > 0,
        )
        already = benunit.sum(person("income_support_reported", period) * cp) > 0
        capital = benunit("income_support_assessable_capital", period)
        return (
            (cp_cares | lone_parent_with_young_child)
            & none_SP_age
            & ~income_related_esa
            & already
            & (capital <= IS.means_test.capital.limit)
        )
