import pandas
import optimizer
from datetime import datetime
from dateutil.relativedelta import relativedelta
from timeit import default_timer


INITIAL_VALUE = 100000
STARTING_DATE = "2010-01-01"
REBALANCE_PERIOD_IN_MONTHS = 12


def backtrade(etf_list, optimizer_parameters, etf_filters, backtrade_parameters):

    initial_value = backtrade_parameters.get("initialValue", INITIAL_VALUE)
    starting_date = backtrade_parameters.get("startingDate", STARTING_DATE)
    rebalance_period = backtrade_parameters.get("rebalancePeriod", REBALANCE_PERIOD_IN_MONTHS)

    start = default_timer()

    value = initial_value
    date = starting_date
    portfolio = []

    while date < datetime.today().date():
        result = optimizer.optimize(etf_list, optimizer_parameters, etf_filters)
        portfolio = result["portfolio"]

        date += relativedelta(months=rebalance_period)
        value = get_portfolio_value_at_date(portfolio, date)

    performance = calculate_performance(starting_date, initial_value, portfolio, value)

    end = default_timer()
    print("Time to run backtrading {}".format(end - start))

    return {"performance": performance, "finalValue": value, "finalPortfolio": portfolio}


def get_portfolio_value_at_date(portfolio, date):
    return 0


def calculate_performance(starting_date, initial_value, portfolio, value):
    return {}
