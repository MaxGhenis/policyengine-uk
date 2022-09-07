from openfisca_uk.model_api import *


class energy_price_cap_subsidy(Variable):
    label = "Energy price cap subsidy"
    documentation = "Reduction in energy bills due to offsetting the price cap and compensating energy firms."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        energy_consumption = household("domestic_energy_consumption", period)
        # For each of the four quarters in the next year, calculate the
        # relative change to the price cap against the baseline price cap,
        # and multiply by quarterly energy consumption.
        total_subsidy = 0
        for quarter in range(1, 5):
            price_cap = parameters(period).gov.ofgem.price_cap[f"{period.start.year}_q{quarter}"]
            baseline_price_cap = parameters(period).baseline.gov.ofgem.price_cap[f"{period.start.year}_q{quarter}"]
            relative_change = (price_cap - baseline_price_cap) / baseline_price_cap
            total_subsidy += -relative_change * energy_consumption / 4
        return total_subsidy