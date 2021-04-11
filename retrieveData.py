import requests
import eikon
import pandas
from ETF import *
import datetime
from pymongo import MongoClient
from timeit import default_timer
from config import EIKON_APP_KEY, JUSTETF_URL, MONGODB_URL

START_DATE = "2000-01-01"


def main():
    etfList = getEtfListFromMongoDB()

    if len(etfList) == 0:
        etfData = getETFData()
        etfList = getETFListFromJson(etfData)
        getRICCodes(etfList)
        saveETFListToMongoDB(etfList)
        etfList = getEtfListFromMongoDB()

    print("Found " + str(len(etfList)) + " ETFs")

    getHistoricalData(etfList)


def getMongoDB():
    client = MongoClient(host="localhost", port=2717)
    # client = MongoClient(MONGODB_URL)
    return client.etfOptimizer


def getEtfListFromMongoDB():
    print("Getting ETFs from MongoDB")
    start = default_timer()
    db = getMongoDB()
    etfs = db.etfs.find()
    etfList = getETFListFromJson(etfs)
    end = default_timer()
    print("Time to get etfList from mongoDB " + str(end - start))
    return etfList


def saveETFListToMongoDB(etfList):
    jsonData = []

    for etf in etfList:
        jsonData.append(etf.toJSON())

    db = getMongoDB()
    db.etfs.insert_many(jsonData)


def updateEtfHistoricalData(etf):
    db = getMongoDB()
    db.etfs.update_one({'_id': etf.getId()}, {'$set': {'historicalData': etf.getHistoricalData()}})


def getETFData():
    print()
    print("Getting all ETFs from justETF")
    
    try:
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        
        body = {
            "country": "DE",
            "draw": "1",
            "start": "0",
            "length": "2000",
            "universeType": "private"
        }

        response = requests.post(JUSTETF_URL, headers=headers, data=body)

        
    except requests.exceptions.RequestException as e:
        print(e)

    responseContent = response.json()

    return responseContent["data"]


def getRICCodes(etfList):
    print()
    print("Get RIC codes from ISIN")

    eikon.set_app_key(EIKON_APP_KEY)

    isinCodes = []

    for etf in etfList:
        isinCodes.append(etf.getIsin())

    RIC_codes = eikon.get_symbology(isinCodes, from_symbol_type="ISIN", to_symbol_type="RIC", bestMatch=False)

    i = 0
    for index, row in RIC_codes.iterrows():
        RICs = row["RICs"]
        etfList[i].setRICs(RICs)
        i += 1


def getHistoricalData(etfList):
    print()
    print("Get historical data for ETFs")

    eikon.set_app_key(EIKON_APP_KEY)

    for i in range(len(etfList)):
        etf = etfList[i]
        if len(etf.getHistoricalData()) > 0:
            continue

        print(str(i) + ": " + etf.getName())

        historicalData = getHistoricalDataForETF(etf)
        if historicalData is None:
            print("Could not get any results for this ETF")
            continue
        else:
            etf.setHistoricalData(historicalData)
            print("Got " + str(len(historicalData)) + " days of data")

        updateEtfHistoricalData(etf)


def getHistoricalDataForETF(etf):
    RICs = etf.getRICs()
    if len(RICs) == 0:
        print("Skipping ETF because it has no RICs")

    for ric in RICs:
        try:
            historicalData = []

            startDate = START_DATE
            endDate = datetime.datetime.now()
            while len(historicalData) % 3000 == 0 and isDateInThePast(startDate):
                data = getDataByRicFromStartDate(ric, startDate, endDate)

                if len(data) == 0:
                    continue

                historicalData = data + historicalData
                endDate = getPreviousDay(data[0]["date"])

            return historicalData

        except Exception as e:
            print(e)
            print("Could not get results for RIC " + ric)


def getPreviousDay(dateString):
    date = datetime.datetime.strptime(dateString, "%Y-%m-%d") - datetime.timedelta(days=1)
    return date.strftime('%Y-%m-%d')


def isDateInThePast(dateString):
    return datetime.datetime.strptime(dateString, "%Y-%m-%d").date() < datetime.datetime.now().date()


def getDataByRicFromStartDate(ric, startDate, endDate):
    result = eikon.get_timeseries(ric, start_date=startDate, end_date=endDate, fields="CLOSE")

    data = []
    for index, row in result.iterrows():
        close = row["CLOSE"]
        if pandas.isna(close):
            close = float("nan")
        data.append({"date": str(index.date()), "close": close})

    return data


if __name__ == "__main__":
    main()