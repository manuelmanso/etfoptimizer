from ETF import get_etf_list_from_json
from pymongo import MongoClient
from timeit import default_timer
import os

MONGO_DB_HOST = os.environ['MONGO_DB_HOST']
MONGO_DB_PORT = int(os.environ['MONGO_DB_PORT'])


def get_mongo_db():
    client = MongoClient(host=MONGO_DB_HOST, port=MONGO_DB_PORT)
    return client.etfOptimizer


def get_etf_list():
    print("Getting ETFs from MongoDB")
    start = default_timer()
    db = get_mongo_db()
    etfs = db.etfs.find()
    etf_list = get_etf_list_from_json(etfs)
    end = default_timer()
    print("Time to get etfList from mongoDB " + str(end - start))
    return etf_list


def save_etf_list(etf_list):
    json_data = []

    for etf in etf_list:
        json_data.append(etf.to_json())

    db = get_mongo_db()
    db.etfs.insert_many(json_data)


def update_etf_historical_data(etf):
    db = get_mongo_db()
    db.etfs.update_one({'_id': etf.get_id()}, {'$set': {'historicalData': etf.get_historical_data()}})
