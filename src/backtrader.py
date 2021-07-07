import optimizer
import ETF
import pandas
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pypfopt
from timeit import default_timer
import matplotlib.pyplot as plt

INITIAL_VALUE = 100000
STARTING_DATE = "2010-01-01"
REBALANCE_PERIOD_IN_MONTHS = 12


def backtrade(etf_list, prices_df, optimizer_parameters, etf_filters, backtrade_parameters):

    initial_value = backtrade_parameters.get("initialValue", INITIAL_VALUE)
    starting_date = backtrade_parameters.get("startingDate", STARTING_DATE)
    rebalance_period = backtrade_parameters.get("rebalancePeriod", REBALANCE_PERIOD_IN_MONTHS)

    optimizer_parameters["nEFPlottingPoints"] = 0  # No need to plot with backtrading

    start = default_timer()

    value = initial_value
    starting_date = datetime.strptime(starting_date, '%Y-%m-%d').date()
    date = starting_date
    trading_history = [{"date": date, "result": None, "value": value}]

    today = datetime.today().date()
    while date < today:
        optimizer_parameters["finalDate"] = date
        optimizer_parameters["initialValue"] = value
        result = optimizer.optimize(etf_list, prices_df, optimizer_parameters, etf_filters)

        next_rebalance = date + relativedelta(months=rebalance_period)

        if next_rebalance > today:
            next_rebalance = today

        while date < next_rebalance:
            date += relativedelta(days=7)

            if date > next_rebalance:
                date = next_rebalance

            value = get_portfolio_value_at_date(prices_df, date, result["portfolio"]) + result["leftoverFunds"]
            trading_history.append({"date": date, "result": result, "value": value})

    risk_free_rate = optimizer_parameters.get("riskFreeRate", optimizer.RISK_FREE_RATE)
    performance = calculate_performance(trading_history, risk_free_rate)

    plot_trading_history(starting_date, initial_value, trading_history, performance)

    end = default_timer()
    print("Time to run backtrading {}".format(end - start))

    return {"performance": performance, "finalValue": value, "tradingHistory": trading_history}


def get_portfolio_value_at_date(prices_df, date, portfolio):
    prices_until_date = prices_df.loc[:str(date)]

    latest_prices = pypfopt.discrete_allocation.get_latest_prices(prices_until_date)

    total_value = 0
    for etf in portfolio:
        etf_identifier = ETF.get_combined_name_and_isin(etf["name"], etf["isin"])

        total_value += latest_prices[etf_identifier] * etf["shares"]

    return total_value


def calculate_performance(trading_history, risk_free_rate):
    starting_date = trading_history[0]["date"]
    end_date = trading_history[-1]["date"]
    initial_value = trading_history[0]["value"]
    end_value = trading_history[-1]["value"]

    years = (end_date - starting_date).days / 365
    annualized_return = ((end_value / initial_value) ** (1 / years) - 1) * 100

    value_history = []
    for history in trading_history:
        value_history.append(history["value"])

    values_df = pandas.DataFrame(value_history)

    cov = pypfopt.risk_models.sample_cov(values_df, frequency=36)
    vol_series = pandas.Series(np.sqrt(np.diag(cov)), index=cov.index)
    volatility = vol_series[0] * 100

    sharpe_ratio = (annualized_return - risk_free_rate*100) / volatility

    return {
        "annualizedReturn": annualized_return,
        "volatility": volatility,
        "sharpeRatio": sharpe_ratio
    }


def plot_trading_history(starting_date, initial_value, trading_history, performance):
    dates = [starting_date]
    values = [initial_value]

    for history in trading_history:
        dates.append(history["date"])
        values.append(history["value"])

    plt.switch_backend('agg')
    plt.plot(dates, values, "-")
    plt.title("Backtrading history")
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value')

    plt.annotate('Annualized return: {0:.2f}%'.format(performance["annualizedReturn"]), xy=(0.05, 0.95), xycoords='axes fraction')
    plt.annotate('Volatility: {0:.2f}%'.format(performance["volatility"]), xy=(0.05, 0.90), xycoords='axes fraction')
    plt.annotate('Sharpe ratio: {0:.2f}'.format(performance["sharpeRatio"]), xy=(0.05, 0.85), xycoords='axes fraction')

    plt.savefig('misc/backtrading.png')
