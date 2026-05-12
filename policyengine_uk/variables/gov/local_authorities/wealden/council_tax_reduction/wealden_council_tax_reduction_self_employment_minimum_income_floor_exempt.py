from policyengine_uk.model_api import *


class wealden_council_tax_reduction_self_employment_minimum_income_floor_exempt(
    Variable
):
    value_type = bool
    entity = Person
    label = "Wealden CTR self-employment minimum income floor exemption"
    documentation = "Whether this person is exempt from Wealden's self-employed minimum income floor because they are within the first year of trading or exceptional circumstances apply."
    definition_period = YEAR
    reference = "https://www.wealden.gov.uk/benefits/who-can-get-council-tax-reduction/"
