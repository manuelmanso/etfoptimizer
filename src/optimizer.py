import pandas
import matplotlib.pyplot as plt
from pypfopt import expected_returns, risk_models, plotting, CLA
from pypfopt.efficient_frontier import EfficientFrontier

from timeit import default_timer

OPTIMIZERS = ["MaxSharpe", "MinimumVolatility", "EfficientRisk", "EfficientReturn"]

OPTIMIZER = "MaxSharpe"
RISK_FREE_RATE = 0.02
REMOVE_TER = True
MINIMUM_DAYS_WITH_DATA = 0
ASSET_WEIGHT_CUTOFF = 0.01
ASSET_WEIGHT_ROUNDING = 4
SHORTING = False
ROLLING_WINDOW_IN_DAYS = 0
MAX_ETF_LIST_SIZE = 400


def optimize(etf_list, optimizer_parameters, etf_filters):

    remove_ter = optimizer_parameters.get("removeTER", REMOVE_TER)
    shorting = optimizer_parameters.get("shorting", SHORTING)
    rolling_window_in_days = optimizer_parameters.get("rollingWindowInDays")
    if rolling_window_in_days is None:
        rolling_window_in_days = ROLLING_WINDOW_IN_DAYS

    etf_list, etfs_matching_filters = filter_etfs_with_size_checks(etf_list, optimizer_parameters, etf_filters)

    start = default_timer()

    prices = get_prices_data_frame(etf_list, rolling_window_in_days)

    returns = expected_returns.mean_historical_return(prices)

    if remove_ter:
        remove_ter_from_returns(etf_list, returns)

    cov = risk_models.sample_cov(prices)

    weight_bounds = (-1, 1) if shorting else (0, 1)
    # solver_options={"max_iter": MAX_ITERATIONS}
    ef = EfficientFrontier(returns, cov, weight_bounds=weight_bounds, solver_options={"solver": "ECOS"}, verbose=True)

    plot = True
    fig, ax = plt.subplots()
    try:
        plotting.plot_efficient_frontier(ef, ax=ax, points=10, show_assets=True)
    except Exception as e:
        plot = False
        print("Error occurred plotting {}".format(str(e)))

    call_optimizer(ef, optimizer_parameters)

    portfolio = get_portfolio_and_performance(ef, optimizer_parameters, etfs_matching_filters)

    if plot:
        plot_ef(portfolio, ax)

    end = default_timer()
    print("Time to find max sharpe {}".format(end - start))

    return portfolio


def filter_etfs_with_size_checks(etf_list, optimizer_parameters, etf_filters):
    max_etf_list_size = optimizer_parameters.get("maxETFListSize", MAX_ETF_LIST_SIZE)

    etf_list = filter_etfs_using_filters(etf_list, etf_filters)
    etf_list_size_after_filtering = len(etf_list)

    if etf_list_size_after_filtering == 0:
        raise Exception("No ETFs are left after filtering. Can't perform portfolio optimization. " +
                        "Check if your filters are correct.")

    if etf_list_size_after_filtering > max_etf_list_size:
        print("Too many ETFs, calculation will take too long. Using only the first {} ETFs".format(max_etf_list_size))
        etf_list = etf_list[:max_etf_list_size]

    return etf_list, etf_list_size_after_filtering


def filter_etfs_using_filters(etf_list, etf_filters):
    minimum_days_with_data = etf_filters.get("minimumDaysWithData")
    if minimum_days_with_data is None:
        minimum_days_with_data = MINIMUM_DAYS_WITH_DATA
    domicile_country = etf_filters.get("domicileCountry", None)
    replication_method = etf_filters.get("replicationMethod", None)
    distribution_policy = etf_filters.get("distributionPolicy", None)

    etfs_with_data = []
    for etf in etf_list:
        if len(etf.get_historical_data()) >= minimum_days_with_data:
            etfs_with_data.append(etf)
    print("Filtered ETFs that don't have enough data: {} ETFs left".format(len(etfs_with_data)))

    etfs_with_filters = []
    for etf in etfs_with_data:

        if domicile_country is not None and domicile_country != etf.get_domicile_country():
            continue

        if replication_method is not None and replication_method != etf.get_replication_method():
            continue

        if distribution_policy is not None and distribution_policy != etf.get_distribution_policy():
            continue

        etfs_with_filters.append(etf)
    print("Filtered ETFs by the parameters provided: {} ETFs left".format(len(etfs_with_filters)))

    return etfs_with_filters


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
        raise Exception("The optimizer provided isn't valid. Provide one of: {}".format(OPTIMIZERS))


def get_portfolio_and_performance(ef, optimizer_parameters, etfs_matching_filters):

    risk_free_rate = optimizer_parameters.get("riskFreeRate", RISK_FREE_RATE)
    asset_cutoff = optimizer_parameters.get("assetCutoff", ASSET_WEIGHT_CUTOFF)
    asset_rounding = optimizer_parameters.get("assetRounding", ASSET_WEIGHT_ROUNDING)

    sharpe_pwt = ef.clean_weights(cutoff=asset_cutoff, rounding=asset_rounding)
    performance = ef.portfolio_performance(risk_free_rate=risk_free_rate)

    portfolio = []
    total = 0
    portfolio_as_dict = dict(sharpe_pwt.items())
    for etf in sorted(portfolio_as_dict, key=portfolio_as_dict.get, reverse=True):
        weight = portfolio_as_dict[etf]
        name = etf.split(" | ")[0]
        isin = etf.split(" | ")[1]
        if weight != 0:
            portfolio.append({"name": name, "isin": isin, "shares": 0, "weight": weight})
            total += weight

    result = {
        "expectedReturn": performance[0],
        "annualVolatility": performance[1],
        "sharpeRatio": performance[2],
        "portfolioSize": len(portfolio),
        "portfolio": portfolio,
        "total": total,
        "matchingFilters": etfs_matching_filters
    }

    return result


def plot_ef(portfolio, ax):
    ax.scatter(portfolio["annualVolatility"], portfolio["expectedReturn"], marker="*", s=100, c="r", label="Optimized Portfolio")
    ax.set_title("Efficient Frontier")
    ax.legend()
    plt.tight_layout()
    plt.savefig("plots/efficientFrontier")


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

        identifier = etf.get_name() + " | " + etf.get_isin()
        prices_by_date[identifier] = prices

    return pandas.DataFrame(prices_by_date)


def get_max_len_historical_data(etf_list):
    max_len = 0
    for etf in etf_list:
        if len(etf.get_historical_data()) > max_len:
            max_len = len(etf.get_historical_data())
    return max_len
