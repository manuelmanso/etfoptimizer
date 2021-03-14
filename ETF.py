class ETF:

    data = {}

    historicalData = []

    def __init__(self, data, historicalData): 
        self.data = data
        self.historicalData = historicalData

    def getData(self):
        return self.data

    def getName(self):
        return self.data["name"]

    def getIsin(self):
        return self.data["isin"]

    def getTicker(self):
        return self.data["ticker"]

    def getRICs(self):
        if "RICs" in self.data:
            return self.data["RICs"]
        return []

    def setRICs(self, rics):
        self.data["RICs"] = rics

    def setHistoricalData(self, historicalData):
        self.historicalData = historicalData

    def getHistoricalData(self):
        return self.historicalData

    def toJSON(self):
        asJson = {
            "data" : self.data,
            "historicalData" : self.historicalData
        }
        return asJson


def getETFListFromJson(jsonData):
    etfList = []

    for d in jsonData:
        if "data" in d and "historicalData" in d:
            etfList.append(ETF(d["data"], d["historicalData"]))
        else:
            etfList.append(ETF(d, {}))

    return etfList

