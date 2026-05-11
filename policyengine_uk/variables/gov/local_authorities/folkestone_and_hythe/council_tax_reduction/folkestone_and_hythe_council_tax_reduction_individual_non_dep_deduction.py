from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class folkestone_and_hythe_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = (
        "Folkestone and Hythe individual Council Tax Reduction non-dependant deduction"
    )
    documentation = "Section 39.5 of the adopted 2026/27 scheme reduces any award by 10 pounds per week for each non-dependant who resides in the dwelling. Section 39.6 waives the deduction where the non-dependant is on income-based Jobseeker's Allowance, income-related Employment Support Allowance, Income Support, Pension Credit (Guarantee Credit), or Universal Credit with no earnings."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.folkestone-hythe.gov.uk/downloads/file/6369/folkestone-hythe-council-tax-reduction-scheme-2026"
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.folkestone_and_hythe.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "folkestone_and_hythe_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        uc_no_earned_income = (person.benunit("universal_credit", period) > 0) & (
            person.benunit.sum(earned_income) <= 0
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | uc_no_earned_income
        )
        return local_scheme * where(
            exempt, 0, ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        )
