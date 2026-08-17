from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_behavioural_response(Variable):
    value_type = float
    entity = Person
    label = "capital gains behavioral response"
    documentation = (
        "Change in realised gains under a reform to the taxation of gains, "
        "given an elasticity of realisations with respect to either the "
        "marginal tax rate or the net-of-tax retention rate."
    )
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        response_parameters = parameters(period).gov.simulation.capital_gains_responses
        mtr_elasticity = response_parameters.elasticity
        retention_elasticity = response_parameters.retention_elasticity

        if mtr_elasticity != 0 and retention_elasticity != 0:
            raise ValueError(
                "gov.simulation.capital_gains_responses.elasticity and "
                "gov.simulation.capital_gains_responses.retention_elasticity "
                "cannot both be nonzero for the same period."
            )

        simulation = person.simulation
        if simulation.baseline is None:
            return 0

        if mtr_elasticity == 0 and retention_elasticity == 0:
            return 0

        capital_gains = person("capital_gains_before_response", period)
        if retention_elasticity != 0:
            relative_change = person("relative_capital_gains_retention_change", period)
            elasticity = person("capital_gains_retention_elasticity", period)
        else:
            relative_change = person("relative_capital_gains_mtr_change", period)
            elasticity = person("capital_gains_elasticity", period)

        response_factor = np.exp(elasticity * relative_change) - 1
        response = capital_gains * response_factor

        return response
