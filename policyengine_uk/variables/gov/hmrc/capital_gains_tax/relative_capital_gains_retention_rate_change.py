from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class relative_capital_gains_retention_rate_change(Variable):
    value_type = float
    entity = Person
    label = "relative change in the capital gains retention rate"
    documentation = (
        "Log change in the share of a marginal pound of gains kept after tax. "
        "The empirical literature estimates realisation elasticities against "
        "this retention rate rather than against the tax rate."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("relative_capital_gains_retention_change", period)
