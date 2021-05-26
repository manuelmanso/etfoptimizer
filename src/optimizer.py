import pandas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pypfopt import expected_returns, risk_models, plotting, discrete_allocation
from pypfopt.efficient_frontier import EfficientFrontier
import base64
import io
import numpy as np
from timeit import default_timer

OPTIMIZERS = ["MaxSharpe", "MinimumVolatility", "EfficientRisk", "EfficientReturn"]

INITIAL_VALUE = 10000
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
    ef = EfficientFrontier(returns, cov, weight_bounds=weight_bounds, solver_options={"solver": "ECOS"}, verbose=True)

    fig, ax = plt.subplots()
    n_points = 10
    param_range = get_plotting_param_range(ef, n_points)
    plotting.plot_efficient_frontier(ef, ax=ax, points=n_points, ef_param_range=param_range, show_assets=True)

    call_optimizer(ef, optimizer_parameters)

    portfolio = get_portfolio_and_performance(ef, prices, optimizer_parameters)
    add_plots_to_portfolio(portfolio, ax, fig)

    end = default_timer()
    print("Time to find max sharpe {}".format(end - start))

    portfolio["ETFsMatchingFilters"] = etfs_matching_filters
    portfolio["ETFsUsedForOptimization"] = len(etf_list)

    return portfolio


def get_plotting_param_range(ef, points):
    param_range = plotting._ef_default_returns_range(ef, points=points)

    if param_range[0] < 0:
        return np.linspace(0, param_range[-1], points)

    return param_range


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
    isin_list = etf_filters.get("isinList", None)
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

        if isin_list is not None and etf.get_isin() not in isin_list:
            continue

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


def get_portfolio_and_performance(ef, prices, optimizer_parameters):

    initial_value = optimizer_parameters.get("initialValue", INITIAL_VALUE)
    risk_free_rate = optimizer_parameters.get("riskFreeRate", RISK_FREE_RATE)
    asset_cutoff = optimizer_parameters.get("assetCutoff", ASSET_WEIGHT_CUTOFF)
    asset_rounding = optimizer_parameters.get("assetRounding", ASSET_WEIGHT_ROUNDING)

    sharpe_pwt = ef.clean_weights(cutoff=asset_cutoff, rounding=asset_rounding)
    performance = ef.portfolio_performance(risk_free_rate=risk_free_rate)

    latest_prices = discrete_allocation.get_latest_prices(prices)
    allocation = discrete_allocation.DiscreteAllocation(sharpe_pwt, latest_prices, initial_value)
    alloc, leftover_funds = allocation.lp_portfolio()

    portfolio = []
    total_weight = 0
    portfolio_as_dict = dict(sharpe_pwt.items())
    for etf in sorted(portfolio_as_dict, key=portfolio_as_dict.get, reverse=True):
        weight = portfolio_as_dict[etf]
        if weight != 0:
            name = etf.split(" | ")[0]
            isin = etf.split(" | ")[1]

            latest_price = latest_prices[etf]
            shares = int(alloc.get(etf, 0))
            value = shares * latest_price

            portfolio.append({"name": name, "isin": isin, "shares": shares, "price": latest_price, "value": value,
                              "weight": weight})
            total_weight += weight

    result = {
        "expectedReturn": performance[0],
        "annualVolatility": performance[1],
        "sharpeRatio": performance[2],
        "portfolioSize": len(portfolio),
        "portfolio": portfolio,
        "totalWeight": total_weight,
        "totalValue": initial_value - leftover_funds,
        "initialValue": initial_value,
        "leftoverFunds": leftover_funds
    }

    return result


def add_plots_to_portfolio(portfolio, ax, fig):
    ax.scatter(portfolio["annualVolatility"], portfolio["expectedReturn"], marker="*", s=100, c="r", label="Optimized Portfolio")
    ax.set_title("Efficient Frontier")
    ax.legend()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    portfolio["efficientFrontierImage"] = base64.b64encode(buf.getbuffer()).decode("ascii")
    buf.close()


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

    total = 0
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
