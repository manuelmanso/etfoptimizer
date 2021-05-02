import requests
import eikon
import pandas
import datetime
from mongoDB import get_etf_list, save_etf_list, update_etf_historical_data
from ETF import *
import os


EIKON_APP_KEY = os.environ['EIKON_APP_KEY']
JUSTETF_URL = os.environ['JUSTETF_URL']

START_DATE = "2000-01-01"


def main():
    etf_list = get_etf_list()

    if len(etf_list) == 0:
        etf_data = get_etf_data()
        etf_list = get_etf_list_from_json(etf_data)
        get_ric_rodes(etf_list)
        save_etf_list(etf_list)
        etf_list = get_etf_list()

    print("Found " + str(len(etf_list)) + " ETFs")

    get_historical_data(etf_list)


def get_etf_data():
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

    json_data = response.json()

    return json_data["data"]


def get_ric_rodes(etf_list):
    print()
    print("Get RIC codes from ISIN")

    eikon.set_app_key(EIKON_APP_KEY)

    isin_codes = []

    for etf in etf_list:
        isin_codes.append(etf.get_isin())

    ric_codes = eikon.get_symbology(isin_codes, from_symbol_type="ISIN", to_symbol_type="RIC", bestMatch=False)

    i = 0
    for index, row in ric_codes.iterrows():
        rics = row["RICs"]
        etf_list[i].set_rics(rics)
        i += 1


def get_historical_data(etf_list):
    print()
    print("Get historical data for ETFs")

    eikon.set_app_key(EIKON_APP_KEY)

    for i in range(len(etf_list)):
        etf = etf_list[i]
        if len(etf.get_historical_data()) > 0:
            continue

        print(str(i) + ": " + etf.get_name())

        historical_data = get_historical_data_for_etf(etf)
        if historical_data is None:
            print("Could not get any results for this ETF")
            continue
        else:
            etf.set_historical_data(historical_data)
            print("Got " + str(len(historical_data)) + " days of data")

        update_etf_historical_data(etf)


def get_historical_data_for_etf(etf):
    rics = etf.get_rics()
    if len(rics) == 0:
        print("Skipping ETF because it has no RICs")

    for ric in rics:
        try:
            historical_data = []

            start_date = START_DATE
            end_date = datetime.datetime.now()
            while len(historical_data) % 3000 == 0 and is_date_in_the_past(start_date):
                data = get_data_by_ric_from_start_date(ric, start_date, end_date)

                if len(data) == 0:
                    continue

                historical_data = data + historical_data
                end_date = get_previous_day(data[0]["date"])

            return historical_data

        except Exception as e:
            print(e)
            print("Could not get results for RIC " + ric)


def get_previous_day(date_string):
    date = datetime.datetime.strptime(date_string, "%Y-%m-%d") - datetime.timedelta(days=1)
    return date.strftime('%Y-%m-%d')


def is_date_in_the_past(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d").date() < datetime.datetime.now().date()


def get_data_by_ric_from_start_date(ric, start_date, end_date):
    result = eikon.get_timeseries(ric, start_date=start_date, end_date=end_date, fields="CLOSE")

    data = []
    for index, row in result.iterrows():
        close = row["CLOSE"]
        if pandas.isna(close):
            close = float("nan")
        data.append({"date": str(index.date()), "close": close})

    return data


if __name__ == "__main__":
    main()
