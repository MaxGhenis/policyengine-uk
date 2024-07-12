from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Housing Benefit means test"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "JSA_income",
            "ESA_income",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = add(benunit, period, INCOME_COMPONENTS)

        personal_benefits = add(benunit, period, ["personal_benefits"])
        # Add personal benefits, credits and total benefits to tax
        credits = add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefits + credits + benefits

        if not bi.interactions.include_in_means_tests:
            # Basic income is already in personal benefits, deduct if needed
            increased_income -= add(benunit, period, ["basic_income"])
        # Reduce increased income by pension contributions and tax
        pension_contributions = (
            add(benunit, period, ["pension_contributions"]) * 0.5
        )
        tax = add(benunit, period, TAX_COMPONENTS)
        increased_income_reduced_by_tax_and_pensions = (
            increased_income - tax - pension_contributions
        )
        disregard = benunit(
            "housing_benefit_applicable_income_disregard", period
        )
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        return max_(
            0,
            increased_income_reduced_by_tax_and_pensions
            - disregard
            - childcare_element,
        )
