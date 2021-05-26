import optimizer


def get_parameters(etf_list):
    domicile_countries = []
    distribution_policies = []
    replication_methods = []
    fund_currencies = []

    for etf in etf_list:
        if etf.get_domicile_country() not in domicile_countries:
            domicile_countries.append(etf.get_domicile_country())
        if etf.get_distribution_policy() not in distribution_policies:
            distribution_policies.append(etf.get_distribution_policy())
        if etf.get_replication_method() not in replication_methods:
            replication_methods.append(etf.get_replication_method())
        if etf.get_fund_currency() not in fund_currencies:
            fund_currencies.append(etf.get_fund_currency())

    return {
        "domicileCountries": domicile_countries,
        "distributionPolicies": distribution_policies,
        "replicationMethods": replication_methods,
        "fundCurrencies": fund_currencies,
        "optimizers": optimizer.OPTIMIZERS
    }
