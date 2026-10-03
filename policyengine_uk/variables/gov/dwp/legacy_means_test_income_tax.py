from policyengine_uk.model_api import *


class legacy_means_test_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax deducted in the legacy means tests"
    documentation = (
        "Income Tax on the income the legacy means tests take into account. The "
        "tests disregard tax only on income they count (Income Support Schedule 9 "
        "paragraph 1; Housing Benefit Schedule 5 paragraph 1; pension-age Housing "
        "Benefit regulation 33(12); Pension Credit regulation 17(10)(a); the "
        "council tax reduction schemes' equivalents), and they treat savings "
        "interest, dividends and property income as capital, not income. So this "
        "is the tax calculated on the person's other income (earned_income_tax, "
        "which covers earnings, pensions and taxable benefits) at Step 4 of "
        "Income Tax Act 2007 s.23, less that income's share of the Step 6 tax "
        "reductions (the married couple's allowance and other tax credits). "
        "Most reductions are not tied to any income: s.27 orders them only to "
        "give the greatest reduction in liability. Some are: foreign tax "
        "credit relief reduces the tax on the income the foreign tax was paid "
        "on (Taxation (International and Other Provisions) Act 2010 ss.18(2) "
        "and 36), and the relief for residential finance costs is given on at "
        "most the property business's profits (Income Tax (Trading and Other "
        "Income) Act 2005 ss.274A and 274AA). The model's other_tax_credits "
        "input mixes these with other reductions (venture capital trust, "
        "enterprise investment and maintenance relief, among others) and "
        "records no source, so the model shares all reductions in proportion "
        "to the Step 4 tax on each kind of income. A credit for foreign tax "
        "on rent is therefore partly attributed to counted income, and the "
        "tax deducted is too low. Step 7 charges, such as the High Income "
        "Child Benefit Charge and the pension annual allowance charge (s.30), "
        "are not tax calculated on any of this income and are not deducted. "
        "The result is income_tax less the tax attributed to capital and the "
        "charges, floored at nil, so a supplied income_tax value flows "
        "through; if it differs from the tax the components imply, the "
        "difference falls on the tax on counted income."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        "https://www.legislation.gov.uk/ukpga/2010/8/section/18",
        "https://www.legislation.gov.uk/ukpga/2010/8/section/36",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274A",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
    ]

    def formula(person, period, parameters):
        # SCRATCH decomposition variant: income tax less the listed components.
        return max_(
            0,
            person("income_tax", period)
            - add(person, period, ['property_income_tax', 'savings_income_tax', 'dividend_income_tax']),
        )
