import requests
import eikon
import pandas
import datetime
from mongoDB import get_etf_list, save_etf_list, update_etf_historical_data, TEST_DB_NAME
from ETF import *
import os
from timeit import default_timer as timer
from concurrent.futures import ThreadPoolExecutor
import math

EIKON_APP_KEY = os.environ['EIKON_APP_KEY']
JUSTETF_URL = os.environ['JUSTETF_URL']

START_DATE = "2000-01-01"

ETFS_PER_ASYNC_REQUEST = int(os.environ.get('ETFS_PER_ASYNC_REQUEST', 1))


def main():
    etf_list = get_etf_list(TEST_DB_NAME)

    if len(etf_list) == 0:
        etf_data = get_etf_data()
        etf_list = get_etf_list_from_json(etf_data)
        get_ric_rodes(etf_list)
        save_etf_list(etf_list, TEST_DB_NAME)
        etf_list = get_etf_list(TEST_DB_NAME)

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
            "length": "4000",
            "universeType": "private",
            "etfsParams": "groupField=index&ls=any"
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

    n_etfs = len(etf_list)
    for i in range(0, n_etfs, ETFS_PER_ASYNC_REQUEST):

        if n_etfs < i + ETFS_PER_ASYNC_REQUEST:
            until = n_etfs
        else:
            until = i + ETFS_PER_ASYNC_REQUEST

        etfs = etf_list[i:until]
        start = timer()
        with ThreadPoolExecutor(max_workers=ETFS_PER_ASYNC_REQUEST) as executor:
            results = executor.map(get_etf_historical_data, etfs)
        added = sum(results)
        end = timer()
        print("Took {}s to get etf data for {} ETFs from eikon".format(end - start, added))

        if added > 0:
            start = timer()
            for etf in etfs:
                update_etf_historical_data(etf, TEST_DB_NAME)
            end = timer()
            print("Took {}s to get write etf data to mongodb. {}-{}".format(end - start, i, until))


def get_etf_historical_data(etf):
    start = timer()
    if etf.get_no_data_found() or len(etf.get_historical_data()) > 0:
        return 0

    rics = etf.get_rics()

    rics_with_data = get_rics_with_data(rics)

    historical_data = []
    found = 3
    ignored = 0
    for ric in rics_with_data:
        try:
            historical_data_tmp = []
            start_date = START_DATE
            end_date = datetime.datetime.now()
            while len(historical_data_tmp) % 3000 == 0 and is_date_in_the_past(start_date):
                data = get_data_by_ric_from_start_date(ric, start_date, end_date)

                if len(data) == 0:
                    break

                historical_data_tmp = data + historical_data_tmp
                end_date = get_previous_day(data[0]["date"])

            if has_only_nans(historical_data_tmp):
                ignored += 1
                continue

            found -= 1

            if len(historical_data_tmp) > len(historical_data):
                historical_data = historical_data_tmp

            if found == 0:
                break

        except Exception as e:
            print("Could not get any data for ric {}".format(ric))

    if len(historical_data) == 0:
        print("Could not get any results for this ETF {}".format(etf.get_name()))
        etf.set_no_data_found()
        etf.set_historical_data([])
        return 1
    else:
        end = timer()
        print("Got {} days of data for ETF {}, took {} and ignored {} results".format(len(historical_data), etf.get_name(), end - start, ignored))
        etf.set_historical_data(historical_data)
        return 1


def has_only_nans(data):
    all_nans = True
    for d in data:
        if not math.isnan(d["close"]):
            all_nans = False
            break
    return all_nans


def is_lacking_data(data):
    """ Returns true if the amount of days with data excluding weekends and holidays is too low.
        Useful to filter out ETFs without good data."""

    inception_date = data[0]["date"]
    date = datetime.datetime.strptime(inception_date, '%Y-%m-%d')
    days_since = (datetime.datetime.today() - date).days

    return len(data) < (days_since * 0.66)


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


def get_rics_with_data(rics):
    if len(rics) == 0:
        return []

    result = eikon.get_timeseries(rics, start_date=-datetime.timedelta(days=30), end_date=datetime.datetime.now(), fields="CLOSE")

    return list(result)


if __name__ == "__main__":
    main()
