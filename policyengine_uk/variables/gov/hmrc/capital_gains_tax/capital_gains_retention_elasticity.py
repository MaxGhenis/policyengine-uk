from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_retention_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of capital gains realizations to the retention rate"
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        gov = parameters(period).gov
        return gov.simulation.capital_gains_responses.retention_elasticity
