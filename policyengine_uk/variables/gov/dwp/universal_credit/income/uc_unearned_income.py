from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    documentation = (
        "Income falling within the descriptions in regulation 66(1) of the "
        "Universal Credit Regulations 2013. Capital counts only through its "
        "assumed yield (uc_tariff_income, regulation 72(1)); actual interest, "
        "dividends and rent are not unearned income at any capital level."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/66"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test
        return add(benunit, period, p.income_definitions.unearned)
