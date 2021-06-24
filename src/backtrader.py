import optimizer
import ETF
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pypfopt
from timeit import default_timer

INITIAL_VALUE = 100000
STARTING_DATE = "2010-01-01"
REBALANCE_PERIOD_IN_MONTHS = 12


def backtrade(etf_list, optimizer_parameters, etf_filters, backtrade_parameters):

    initial_value = backtrade_parameters.get("initialValue", INITIAL_VALUE)
    starting_date = backtrade_parameters.get("startingDate", STARTING_DATE)
    rebalance_period = backtrade_parameters.get("rebalancePeriod", REBALANCE_PERIOD_IN_MONTHS)

    optimizer_parameters["nEFPlottingPoints"] = 0  # No need to plot with backtrading

    start = default_timer()

    value = initial_value
    date = datetime.strptime(starting_date, '%Y-%m-%d').date()
    trading_history = []
    result = {}

    today = datetime.today().date()
    while date < today:
        optimizer_parameters["finalDate"] = date
        optimizer_parameters["initialValue"] = value
        result = optimizer.optimize(etf_list, optimizer_parameters, etf_filters)

        date += relativedelta(months=rebalance_period)

        if date > today:
            date = today

        filtered_etf_list, _ = optimizer.filter_etfs_with_size_checks(etf_list, optimizer_parameters, etf_filters)
        value = get_portfolio_value_at_date(filtered_etf_list, result["portfolio"], date) + result["leftoverFunds"]

        trading_history.append({"date": date, "result": result, "value": value})

    performance = calculate_performance(starting_date, today, initial_value, result, value)

    plot_trading_history(starting_date, today, initial_value, trading_history)

    end = default_timer()
    print("Time to run backtrading {}".format(end - start))

    return {"performance": performance, "finalValue": value, "finalPortfolio": result.get("portfolio", [])}


def get_portfolio_value_at_date(etf_list, portfolio, date):

    prices = optimizer.get_prices_data_frame(etf_list, 0, date)  # Only do this for applicable ETFs

    latest_prices = pypfopt.discrete_allocation.get_latest_prices(prices)

    total_value = 0
    for etf in portfolio:
        etf_identifier = ETF.get_combined_name_and_isin(etf["name"], etf["isin"])

        total_value += latest_prices[etf_identifier] * etf["shares"]

    return total_value


def calculate_performance(starting_date, end_date, initial_value, portfolio, value):
    return {}


def plot_trading_history(starting_date, end_date, initial_value, trading_history):
    pass
