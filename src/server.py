import flask
from flask_cors import CORS
from waitress import serve
import optimizer
from mongoDB import get_etf_list, PRODUCTION_DB_NAME
import backtrader
import parameters

app = flask.Flask(__name__)
CORS(app)

full_etf_list = get_etf_list(PRODUCTION_DB_NAME)
parameters = parameters.get_parameters(full_etf_list)


@app.route('/api/optimize', methods=["POST"])
def optimize():
    try:
        body = flask.request.json
        optimizer_parameters = body.get("optimizerParameters", {})
        etf_filters = body.get("etfFilters", {})
        return optimizer.optimize(full_etf_list, optimizer_parameters, etf_filters)
    except Exception as e:
        print("Exception: ", e)
        return {"error": str(e)}, 400


@app.route('/api/backtrade', methods=["POST"])
def backtrade():
    try:
        body = flask.request.json
        optimizer_parameters = body.get("optimizerParameters", {})
        etf_filters = body.get("etfFilters", {})
        backtrade_parameters = body.get("backtradeParameters", {})
        return backtrader.backtrade(full_etf_list, optimizer_parameters, etf_filters, backtrade_parameters)
    except Exception as e:
        print("Exception: ", e)
        return {"error": str(e)}, 400


@app.route('/api/etfsMatchingFilters', methods=["POST"])
def get_etfs_matching_filters():
    try:
        body = flask.request.json
        etf_filters = body.get("etfFilters", {})
        filtered_etfs = optimizer.filter_etfs_using_filters(full_etf_list, etf_filters)
        return {"etfsMatchingFilters": len(filtered_etfs), "totalETFs": len(full_etf_list)}
    except Exception as e:
        print("Exception: ", e)
        return {"error": str(e)}, 400


@app.route('/api/parameters', methods=["GET"])
def get_parameters():
    try:
        return parameters
    except Exception as e:
        print("Exception: ", e)
        return {"error": str(e)}, 400


@app.route('/etfList', methods=["GET"])
def get_etf_list():
    try:
        etf_json_list = []
        for etf in full_etf_list:
            etf_as_json = etf.get_data()
            etf_as_json["daysWithData"] = len(etf.get_historical_data())
            etf_json_list.append(etf_as_json)
        return {"etfList": etf_json_list}
    except Exception as e:
        print("Exception: ", e)
        return {"error": str(e)}, 400


if __name__ == '__main__':
    serve(app, host="0.0.0.0")
