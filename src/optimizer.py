import pandas
import os
from mongoDB import get_etf_list
from pypfopt import expected_returns
from pypfopt import risk_models
from pypfopt.efficient_frontier import EfficientFrontier
from timeit import default_timer

MAX_ETF_LIST_SIZE = int(os.environ.get('MAX_ETF_LIST_SIZE', -1))

OPTIMIZERS = ["MaxSharpe", "MinimumVolatility", "EfficientRisk", "EfficientReturn"]

OPTIMIZER = "MaxSharpe"

RISK_FREE_RATE = 0.02
REMOVE_TER = True
MINIMUM_DAYS_WITH_DATA = 500  # around 2 years
ASSET_WEIGHT_CUTOFF = 0.01
ASSET_WEIGHT_ROUNDING = 4
SHORTING = False
ROLLING_WINDOW_IN_DAYS = 0


full_etf_list = get_etf_list()


def optimize(optimizer_parameters, etf_filters):

    global full_etf_list

    remove_ter = optimizer_parameters.get("removeTER", REMOVE_TER)
    shorting = optimizer_parameters.get("shorting", SHORTING)
    rolling_window_in_days = optimizer_parameters.get("rollingWindowInDays", ROLLING_WINDOW_IN_DAYS)

    etf_list = filter_etfs_without_data(full_etf_list, optimizer_parameters)

    etf_list = filter_etfs(etf_list, etf_filters)

    if len(etf_list) == 0:
        raise Exception("No ETFs are left after filtering. Can't perform portfolio optimization.")

    if len(etf_list) > 1 and MAX_ETF_LIST_SIZE != -1:
        print("Too many ETFs, calculation will take too long. Using only the first {} ETFs".format(MAX_ETF_LIST_SIZE))
        etf_list = etf_list[:MAX_ETF_LIST_SIZE]

    start = default_timer()

    prices = get_prices_data_frame(etf_list, rolling_window_in_days)

    returns = expected_returns.mean_historical_return(prices)

    if remove_ter:
        remove_ter_from_returns(etf_list, returns)

    cov = risk_models.sample_cov(prices)

    weight_bounds = (-1, 1) if shorting else (0, 1)
    ef = EfficientFrontier(returns, cov, weight_bounds=weight_bounds, solver_options={"max_iter": 100000}, verbose=True)

    call_optimizer(ef, optimizer_parameters)

    portfolio = get_portfolio_and_performance(ef, optimizer_parameters)
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


def call_optimizer(ef, optimizer_parameters):
    optimizer = optimizer_parameters.get("optimizer", OPTIMIZER)
    target_volatility = optimizer_parameters.get("targetVolatility", None)
    target_return = optimizer_parameters.get("targetReturn", None)
    risk_free_rate = optimizer_parameters.get("riskFreeRate", RISK_FREE_RATE)

    if optimizer == "MaxSharpe":
        ef.max_sharpe(risk_free_rate=risk_free_rate)

    elif optimizer == "MinimumVolatility":
        ef.min_volatility()

    elif optimizer == "EfficientRisk":
        if target_volatility is None:
            raise Exception("No target volatility provided for EfficientRisk optimizer.")

        ef.efficient_risk(target_volatility=target_volatility)

    elif optimizer == "EfficientReturn":
        if target_return is None:
            raise Exception("No target return provided for EfficientReturn optimizer.")

        ef.efficient_return(target_return=target_return)

    else:
        raise Exception("No optimizer was provided. Provide one of: {}".format(OPTIMIZERS))


def get_portfolio_and_performance(ef, optimizer_parameters):

    risk_free_rate = optimizer_parameters.get("riskFreeRate", RISK_FREE_RATE)
    asset_cutoff = optimizer_parameters.get("assetCutoff", ASSET_WEIGHT_CUTOFF)
    asset_rounding = optimizer_parameters.get("assetRounding", ASSET_WEIGHT_ROUNDING)

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


def get_prices_data_frame(etf_list, rolling_window_in_days):
    prices = get_prices_data_frame_full_history(etf_list)
    if rolling_window_in_days > 0:
        prices = prices[-rolling_window_in_days:]

    return prices


def get_prices_data_frame_full_history(etf_list):
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
