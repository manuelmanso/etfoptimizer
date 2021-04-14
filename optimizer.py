import pandas
from retrieveData import getEtfListFromMongoDB
from pypfopt import expected_returns
from pypfopt import risk_models
from pypfopt.efficient_frontier import EfficientFrontier
from timeit import default_timer

RISK_FREE_RATE = 0.02

REMOVE_TER = True

MINIMUM_DAYS_WITH_DATA = 500  # around 2 years

ASSET_WEIGHT_CUTOFF = 0.01
ASSET_WEIGHT_ROUNDING = 4


fullETFList = getEtfListFromMongoDB()


def optimize():

    global fullETFList

    etfList = fullETFList[0:100]

    etfList = filterDatalessETFs(etfList)

    etfList = filterETFsByParameters(etfList)

    return findMaxSharpePortfolio(etfList)


def filterDatalessETFs(etfList):
    etfsWithData = []

    for etf in etfList:
        if len(etf.getHistoricalData()) >= MINIMUM_DAYS_WITH_DATA:
            etfsWithData.append(etf)

    print("Filtered ETFs that don't have enough data or aren't traded anymore: " + str(len(etfsWithData)) + " ETFs left")
    return etfsWithData


def filterETFsByParameters(etfList):
    etfsByParams = []

    for etf in etfList:
        etfsByParams.append(etf)

    print("Filtered ETFs by the parameters provided: " + str(len(etfsByParams)) + " ETFs left")
    return etfsByParams


def findMaxSharpePortfolio(etfList):

    prices = getPricesDataFrame(etfList)

    returns = expected_returns.mean_historical_return(prices)

    if REMOVE_TER:
        removeTERFromReturns(etfList, returns)

    start = default_timer()
    cov = risk_models.sample_cov(prices)
    end = default_timer()
    print("Time to get covariance " + str(end - start))

    ef = EfficientFrontier(returns, cov, weight_bounds=(0, 1), solver_options={"max_iter": 100000}, verbose=True)

    start = default_timer()
    ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
    end = default_timer()
    print("Time to find max sharpe " + str(end - start))

    sharpe_pwt = ef.clean_weights(cutoff=ASSET_WEIGHT_CUTOFF, rounding=ASSET_WEIGHT_ROUNDING)
    performance = ef.portfolio_performance(verbose=True, risk_free_rate=RISK_FREE_RATE)

    portfolio = {}
    total = 0
    for key, value in sharpe_pwt.items():
        if value > 0:
            portfolio[key] = value
            total += value

    print(str(len(portfolio.keys())) + " assets:", portfolio)
    print("Total:", total)

    result = {
        "expected return": performance[0],
        "annual volatility": performance[1],
        "sharpe ratio": performance[2],
        "portfolio": portfolio
    }

    return result


def removeTERFromReturns(etfList, returns):

    for index, row in returns.items():
        for etf in etfList:
            if etf.getName() == index:
                returns.loc[index] = row - etf.getTER()


def getPricesDataFrame(etfList):
    pricesByDate = {}

    maxSize = 0
    for etf in etfList:
        if len(etf.getHistoricalData()) > maxSize:
            maxSize = len(etf.getHistoricalData())

    for etf in etfList:
        prices = []
        for datePrice in etf.getHistoricalData():
            price = datePrice["close"]
            if price == 0:  # Fixes ETFs that have 0 as their first value and then get an infinite return
                prices.append(float("nan"))
            else:
                prices.append(price)

        if len(prices) < maxSize:  # adds "NaNs" at the start of the list
            nans = [float("nan")] * (maxSize - len(prices))
            prices = nans + prices

        # identifier = etf.getName() + " - " + etf.getIsin()
        identifier = etf.getName()
        pricesByDate[identifier] = prices

    return pandas.DataFrame(pricesByDate)