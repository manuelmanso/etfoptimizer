import flask
import optimizer
import os
from mongoDB import get_etf_list
import parameters

OPTIMIZER_CONTAINER_PORT = int(os.environ['OPTIMIZER_CONTAINER_PORT'])

app = flask.Flask(__name__)

full_etf_list = get_etf_list()
parameters = parameters.get_parameters(full_etf_list)


@app.route('/optimize', methods=["GET"])
def optimize():
    try:
        body = flask.request.json
        result = optimizer.optimize(full_etf_list, body["optimizerFilters"], body["etfFilters"])
        return result
    except Exception as e:
        return str(e), 400


@app.route('/parameters', methods=["GET"])
def get_parameters():
    return parameters


@app.route('/etfList', methods=["GET"])
def get_eft_list():
    etf_json_list = []

    for etf in full_etf_list:
        etf_as_json = etf.get_data()
        etf_as_json["daysWithData"] = len(etf.get_historical_data())
        etf_json_list.append(etf_as_json)

    return {"etfList": etf_json_list}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=OPTIMIZER_CONTAINER_PORT)
