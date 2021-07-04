import pandas
import matplotlib.pyplot as plt
from ETF import get_split_name_and_isin, get_combined_name_and_isin
from pypfopt import expected_returns, risk_models, plotting, discrete_allocation
from pypfopt.efficient_frontier import EfficientFrontier
from datetime import datetime
import base64
import io
import numpy as np
import math
from timeit import default_timer

OPTIMIZERS = ["MaxSharpe", "MinimumVolatility", "EfficientRisk", "EfficientReturn"]

INITIAL_VALUE = 10000
OPTIMIZER = "MaxSharpe"
RISK_FREE_RATE = 0.02
MINIMUM_DAYS_WITH_DATA = 0
ASSET_WEIGHT_CUTOFF = 0.01
ASSET_WEIGHT_ROUNDING = 4
ROLLING_WINDOW_IN_DAYS = 0
MAX_ETF_LIST_SIZE = 400
N_EF_PLOTTING_POINTS = 10


def optimize(etf_list, optimizer_parameters, etf_filters):

    etf_list, etfs_matching_filters = filter_etfs_with_size_checks(etf_list, optimizer_parameters, etf_filters)

    start = default_timer()

    rolling_window_in_days = optimizer_parameters.get("rollingWindowInDays", ROLLING_WINDOW_IN_DAYS)
    final_date = optimizer_parameters.get("finalDate", None)
    prices = get_prices_data_frame(etf_list, rolling_window_in_days, final_date)

    returns = expected_returns.mean_historical_return(prices)
    remove_ter_from_returns(etf_list, returns)

    cov = risk_models.sample_cov(prices)
    volatility = pandas.Series(np.sqrt(np.diag(cov)), index=cov.index)

    ef = EfficientFrontier(returns, cov, weight_bounds=(0, 1), solver_options={"solver": "ECOS"}, verbose=False)

    n_ef_plotting_points = optimizer_parameters.get("nEFPlottingPoints", N_EF_PLOTTING_POINTS)

    if n_ef_plotting_points > 0:
        fig, ax = plt.subplots()
        param_range = get_plotting_param_range(ef, n_ef_plotting_points)
        plotting.plot_efficient_frontier(ef, ax=ax, points=n_ef_plotting_points, ef_param_range=param_range, show_assets=True)

        call_optimizer(ef, optimizer_parameters)

        portfolio = get_portfolio_and_performance(ef, prices, optimizer_parameters, returns, volatility)

        plot_assets_in_portfolio_with_different_color(portfolio, ax, volatility, returns)
        add_plot_to_portfolio(portfolio, ax, fig)
    else:
        call_optimizer(ef, optimizer_parameters)

        portfolio = get_portfolio_and_performance(ef, prices, optimizer_parameters, returns, volatility)

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

    if etf_list_size_after_filtering == 1:
        raise Exception("Can't perform portfolio optimization on just one ETF.")

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
    fund_currency = etf_filters.get("fundCurrency", None)

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

        if fund_currency is not None and fund_currency != etf.get_fund_currency():
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


def get_portfolio_and_performance(ef, prices, optimizer_parameters, returns, variance):

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
            name, isin = get_split_name_and_isin(etf)

            latest_price = latest_prices[etf]
            shares = int(alloc.get(etf, 0))
            value = shares * latest_price

            expected_return = returns[etf]
            volatility = variance[etf]

            portfolio.append({"name": name, "isin": isin, "shares": shares, "price": latest_price, "value": value,
                              "expectedReturn": expected_return, "volatility": volatility, "weight": weight})
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


def plot_assets_in_portfolio_with_different_color(portfolio, ax, volatility, returns):
    volatility_list = []
    return_list = []

    for etf in portfolio["portfolio"]:
        etf_combined_name = get_combined_name_and_isin(etf["name"], etf["isin"])

        volatility_list.append(volatility[etf_combined_name])
        return_list.append(returns[etf_combined_name])

    ax.scatter(
        volatility_list,
        return_list,
        s=30,
        color="g",
        label="assets in portfolio",
    )


def add_plot_to_portfolio(portfolio, ax, fig):
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


def get_prices_data_frame(etf_list, rolling_window_in_days, final_date):
    prices_by_date = {}

    for etf in etf_list:

        if len(etf.get_historical_data()) == 0:
            continue

        identifier = get_combined_name_and_isin(etf.get_name(), etf.get_isin())

        dates = {}
        historical_data = etf.get_historical_data()
        last_50 = []
        for i in range(len(historical_data)):
            date_price = historical_data[i]

            date = date_price["date"]
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            if final_date is not None and date_obj > final_date:
                break

            price = date_price["close"]

            # Fixes ETFs that have 0 as their first value and then get an infinite return
            if price == 0:
                price = float("nan")

            # Fixes ETFs that have 1 day with a completely wrong value
            previous_price = historical_data[i-1]["close"] if i > 0 else float("nan")
            next_price = historical_data[i+1]["close"] if i < len(historical_data) - 1 else float("nan")
            if not math.isnan(previous_price) and previous_price != 0 and (0.2 > (price / previous_price) or 5 < (price / previous_price)):
                price = float("nan")
            elif not math.isnan(next_price) and next_price != 0 and (0.2 > (price / next_price) or 5 < (price / next_price)):
                price = float("nan")
            elif len(last_50) > 0:
                last_50_avg = sum(last_50) / len(last_50)
                if 0.2 > (price / last_50_avg) or 5 < (price / last_50_avg):
                    price = float("nan")

            if not math.isnan(price):
                last_50.append(price)

            if len(last_50) == 50:
                last_50 = last_50[1:]

            dates[date] = price

        prices_by_date[identifier] = dates

    df = pandas.DataFrame(prices_by_date)
    df.sort_index(inplace=True)
    df = df[-rolling_window_in_days:]

    # Only include ETFs that have at least two recorded prices in the given timeframe, otherwise there are errors
    etfs_to_drop = []
    for etf in df:
        at_least_two_prices = 0
        for price in df[etf][::-1]:
            if not math.isnan(price):
                at_least_two_prices += 1

            if at_least_two_prices == 2:
                break

        if at_least_two_prices < 2:
            etfs_to_drop.append(etf)

    return df.drop(etfs_to_drop, 1)
