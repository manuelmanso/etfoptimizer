import flask
import optimizer
import os

OPTIMIZER_CONTAINER_PORT = int(os.environ['OPTIMIZER_CONTAINER_PORT'])

app = flask.Flask(__name__)


@app.route('/optimize', methods=["GET"])
def optimize():
    try:
        body = flask.request.json
        result = optimizer.optimize(body["optimizerFilters"], body["etfFilters"])
        return result
    except Exception as e:
        return str(e), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=OPTIMIZER_CONTAINER_PORT)