import pandas
from mongoDB import get_etf_list
from pypfopt import expected_returns
from pypfopt import risk_models
from pypfopt.efficient_frontier import EfficientFrontier
from timeit import default_timer

RISK_FREE_RATE = 0.02
REMOVE_TER = True
MINIMUM_DAYS_WITH_DATA = 500  # around 2 years
ASSET_WEIGHT_CUTOFF = 0.01
ASSET_WEIGHT_ROUNDING = 4
SHORTING = False


full_etf_list = get_etf_list()


def optimize(optimizer_parameters, etf_filters):

    global full_etf_list

    etf_list = filter_etfs_without_data(full_etf_list, optimizer_parameters)

    etf_list = filter_etfs(etf_list, etf_filters)

    if len(etf_list) == 0:
        raise Exception("No ETFs are left after filtering. Can't perform portfolio optimization.")

    start = default_timer()
    portfolio = find_max_sharpe_portfolio(etf_list, optimizer_parameters)
    end = default_timer()
    print("Time to find max sharpe {}".format(end - start))

    return portfolio


def filter_etfs_without_data(etf_list, optimizer_parameters):
    etfs_with_data = []

    minimum_days_with_data = optimizer_parameters.get("minimumDaysWithData")

    for etf in etf_list:
        if len(etf.get_historical_data()) >= minimum_days_with_data:
            etfs_with_data.append(etf)

    print("Filtered ETFs that don't have enough data: {} ETFs left".format(len(etfs_with_data)))
    return etfs_with_data


def filter_etfs(etf_list, etf_filters):
    etfs = []

    domicile_country = etf_filters.get("domicileCountry")
    replication_method = etf_filters.get("replicationMethod")
    distribution_policy = etf_filters.get("distributionPolicy")

    for etf in etf_list:

        if domicile_country and domicile_country != etf.get_domicile_country():
            continue

        if replication_method and replication_method != etf.get_replication_method():
            continue

        if distribution_policy and distribution_policy != etf.get_distribution_policy():
            continue

        etfs.append(etf)

    print("Filtered ETFs by the parameters provided: {} ETFs left".format(len(etfs)))
    return etfs


def find_max_sharpe_portfolio(etf_list, optimize_parameters):

    asset_cutoff = optimize_parameters.get("assetCutoff", ASSET_WEIGHT_CUTOFF)
    asset_rounding = optimize_parameters.get("assetRounding", ASSET_WEIGHT_ROUNDING)
    remove_ter = optimize_parameters.get("removeTER", REMOVE_TER)
    risk_free_rate = optimize_parameters.get("riskFreeRate", RISK_FREE_RATE)
    shorting = optimize_parameters.get("shorting", SHORTING)

    prices = get_prices_data_frame(etf_list)

    returns = expected_returns.mean_historical_return(prices)

    if remove_ter:
        remove_ter_from_returns(etf_list, returns)

    cov = risk_models.sample_cov(prices)

    weight_bounds = (-1, 1) if shorting else (0, 1)
    ef = EfficientFrontier(returns, cov, weight_bounds=weight_bounds, solver_options={"max_iter": 100000})

    ef.max_sharpe(risk_free_rate=risk_free_rate)

    sharpe_pwt = ef.clean_weights(cutoff=asset_cutoff, rounding=asset_rounding)
    performance = ef.portfolio_performance(risk_free_rate=risk_free_rate)

    portfolio = {}
    total = 0
    for key, value in sharpe_pwt.items():
        if value != 0:
            portfolio[key] = value
            total += value

    result = {
        "expected return": performance[0],
        "annual volatility": performance[1],
        "sharpe ratio": performance[2],
        "portfolio": portfolio,
        "total": total
    }

    return result


def remove_ter_from_returns(etf_list, returns):

    for index, row in returns.items():
        for etf in etf_list:
            if etf.get_name() == index:
                returns.loc[index] = row - etf.get_ter()


def get_prices_data_frame(etf_list):
    prices_by_date = {}

    max_len = get_max_len_historical_data(etf_list)

    for etf in etf_list:
        prices = []
        for datePrice in etf.get_historical_data():
            price = datePrice["close"]
            if price == 0:  # Fixes ETFs that have 0 as their first value and then get an infinite return
                prices.append(float("nan"))
            else:
                prices.append(price)

        if len(prices) < max_len:  # adds "NaNs" at the start of the list
            nans = [float("nan")] * (max_len - len(prices))
            prices = nans + prices

        # identifier = etf.get_name() + " - " + etf.get_isin()
        identifier = etf.get_name()
        prices_by_date[identifier] = prices

    return pandas.DataFrame(prices_by_date)


def get_max_len_historical_data(etf_list):
    max_len = 0
    for etf in etf_list:
        if len(etf.get_historical_data()) > max_len:
            max_len = len(etf.get_historical_data())
    return max_len
