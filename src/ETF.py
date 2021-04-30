class ETF:

    _id = ""
    data = {}
    historical_data = []

    def __init__(self, _id, data, historical_data):
        self._id = _id
        self.data = data
        self.historical_data = historical_data

    def get_id(self):
        return self._id

    def get_data(self):
        return self.data

    def get_name(self):
        return self.data["name"]

    def get_isin(self):
        return self.data["isin"]

    def get_ticker(self):
        return self.data["ticker"]

    def get_ter(self):
        return float(self.data["ter"][:-1]) * 0.01

    def get_domicile_country(self):
        return self.data["domicileCountry"]

    def get_replication_method(self):
        return self.data["replicationMethod"]

    def get_distribution_policy(self):
        return self.data["distributionPolicy"]

    def get_rics(self):
        if "RICs" in self.data:
            return self.data["RICs"]
        return []

    def set_rics(self, rics):
        self.data["RICs"] = rics

    def set_historical_data(self, historical_data):
        self.historical_data = historical_data

    def get_historical_data(self):
        return self.historical_data

    def to_json(self):
        as_json = {
            "data": self.data,
            "historicalData": self.historical_data
        }
        return as_json


def get_etf_list_from_json(json_data):
    etf_list = []

    for d in json_data:
        if "_id" in d and "data" in d and "historicalData" in d:
            etf_list.append(ETF(d["_id"], d["data"], d["historicalData"]))
        else:
            etf_list.append(ETF("", d, {}))

    return etf_list

