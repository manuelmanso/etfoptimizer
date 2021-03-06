from ETF import get_etf_list_from_json
from pymongo import MongoClient
from timeit import default_timer
import os

MONGO_DB_HOST = os.environ.get('MONGO_DB_HOST')
MONGO_DB_PORT = int(os.environ.get('MONGO_DB_PORT', 2717))

TEST_DB_NAME = "test"
PRODUCTION_DB_NAME = "prod"


def get_mongo_client():
    if MONGO_DB_HOST is not None:
        return MongoClient(host=MONGO_DB_HOST, port=MONGO_DB_PORT)
    else:
        return MongoClient("mongodb://mongo-service:2717")


def get_etf_list(db_name):
    print("Getting ETFs from MongoDB")
    start = default_timer()
    db = get_mongo_client()[db_name]
    etfs = db.etfs.find(allow_disk_use=True).sort("data.yearReturnPerRiskCUR", -1)
    etf_list = get_etf_list_from_json(etfs)
    end = default_timer()
    print("Time to get etfList from mongoDB " + str(end - start))
    return etf_list


def get_etf_list_with_historical_data(db_name):
    etf_list = get_etf_list(db_name)
    etf_list_with_data = []

    for etf in etf_list:
        if len(etf.get_historical_data()) > 0:
            etf_list_with_data.append(etf)

    return etf_list_with_data


def save_etf_list(etf_list, db_name):
    json_data = []

    for etf in etf_list:
        json_data.append(etf.to_json())

    db = get_mongo_client()[db_name]
    db.etfs.insert_many(json_data)


def update_etf_historical_data(etf, db_name):
    db = get_mongo_client()[db_name]
    db.etfs.update_one({'_id': etf.get_id()}, {'$set': {'historicalData': etf.get_historical_data()}})


def clear_test_db():
    client = get_mongo_client()
    client.drop_database(TEST_DB_NAME)
