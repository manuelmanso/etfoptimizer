import requests
import eikon
import pandas
from ETF import *
import json

EIKON_APP_KEY = '10d6c70fb1ab4eeab8211ea6793548258f8f6e09'
ETF_DATA_FILENAME = 'etfData.json'

def main():
    etfData = loadDataFromFile()

    if len(etfData) == 0:
        etfData = getETFData()
        saveDataToFile(etfData)

    print("Found " + str(len(etfData)) + " ETFs")

    etfList = getETFListFromJson(etfData)

    getRICCodes(etfList)

    getHistoricalData(etfList)

    checkMissingHistoricalData(etfList)


def loadDataFromFile():
    print()
    try:
        with open(ETF_DATA_FILENAME) as json_file:
            print("Load ETF data from file")
            return json.load(json_file)
    except:
        print("Could not load data from file")
        return []


def saveDataToFile(etfData):
    print("Saving etf data to file")
    with open(ETF_DATA_FILENAME, 'w') as json_file:
        json.dump(etfData, json_file, indent=4)

def saveETFListToFile(etfList):
    etfData = []
    for etf in etfList:
        etfData.append(etf.toJSON())
    saveDataToFile(etfData)


def getETFData():
    print()
    print("Getting all ETFs from justETF")

    justEftUrl = "https://www.justetf.com/servlet/etfs-table"
    
    try:
        headers={
            "content-type":"application/x-www-form-urlencoded"
        }
        
        body = {
            "country": "DE",
            "draw":"1",
            "start":"0",
            "length":"2000",
            "universeType":"private"
        }

        response = requests.post(justEftUrl, headers=headers, data=body)

        
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
        rics = row["RICs"]
        etfList[i].setRICs(rics)
        i+=1

    saveETFListToFile(etfList)


def getHistoricalData(etfList):
    print()
    print("Get historical data for ETFs")

    eikon.set_app_key(EIKON_APP_KEY)

    updatedCounter = 0
    for i in range(len(etfList)):
        etf = etfList[i]
        print(str(i) + ": " + etf.getName())

        if len(etf.getHistoricalData()) > 0:
            print("Skipping ETF " + etf.getName() + " since it already has historical data")
            continue

        historicalData = getHistoricalDataForETF(etf)
        if historicalData is None:
            print("Could not get any results for this ETF")
            continue

        print("Found " + str(len(historicalData)) + " weeks of data")
        etf.setHistoricalData(historicalData)

        if updatedCounter % 25 == 0 and updatedCounter != 0:
            saveETFListToFile(etfList)

        updatedCounter+=1

    saveETFListToFile(etfList)


def getHistoricalDataForETF(etf):
    rics = etf.getRICs()
    if len(rics) == 0:
        print("Skipping ETF because it has no RICs")

    for ric in rics:
        try:
            result = eikon.get_timeseries(ric, start_date="2000-01-01", fields="CLOSE", interval='weekly')

            historicalData = []
            for index, row in result.iterrows():
                if not pandas.isna(row["CLOSE"]):
                    historicalData.append({"date": str(index.date()), "close": row["CLOSE"]})

            if len(historicalData) > 0:
                return historicalData
        except:
            print("Could not get results for RIC " + ric)


def checkMissingHistoricalData(etfList):

    missingCounter = 0
    lessThan50Counter = 0
    lessThan100Counter = 0

    for i in range(len(etfList)):
        etf=etfList[i]
        if len(etf.getHistoricalData()) == 0:
            print(i, etf.getName())
            missingCounter+=1
        if len(etf.getHistoricalData()) < 50:
            lessThan50Counter+=1
        if len(etf.getHistoricalData()) < 100:
            lessThan100Counter+=1


    print(str(missingCounter) + " ETFs are missing historicalData")
    print(str(lessThan50Counter) + " ETFs have less than 50 weeks of historical data")
    print(str(lessThan100Counter) + " ETFs have less than 100 weeks of historical data")


if __name__ == "__main__":
    main()